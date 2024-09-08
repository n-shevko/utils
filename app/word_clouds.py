import os
import json
import re

from app import text_image_feedback_spiral

from app.utils import get, update, each_slice
from app.models import Word, WordFreqs, Lists
from channels.db import database_sync_to_async

from datetime import datetime

import pymupdf
import spacy


class Worker(text_image_feedback_spiral.Worker):
    async def word_clouds_context(self, _):
        await self.load_top_by_years()

    @database_sync_to_async
    def extract_words_from_text(self, text, file, nlp):
        doc = nlp(text)
        tmp = []
        re_pattern = re.compile(u'[^\u0000-\uD7FF\uE000-\uFFFF]', re.UNICODE)
        for token in doc:
            if not token.is_alpha:
                continue

            tmp.append(
                Word(
                    original=re_pattern.sub(u'\uFFFD', token.text),
                    lemma=re_pattern.sub(u'\uFFFD', token.lemma_),
                    source_file=file,
                    part_of_speech=token.pos_
                )
            )
        if tmp:
            try:
                Word.objects.bulk_create(tmp)
            except Exception as _:
                raise Exception(f"Can't import page from file {file}")

    @database_sync_to_async
    def count_freqs(self, year_to_source_files):
        year_to_source_files2 = {}
        for item in year_to_source_files:
            year_to_source_files2.setdefault(int(item['year']), []).append(item['file'])

        WordFreqs.objects.all().delete()

        for year, files in year_to_source_files2.items():
            freqs = {}
            for word in Word.objects.filter(source_file__in=files):
                key = (word.lemma, word.part_of_speech)
                freqs[key] = freqs.get(key, 0) + 1

            tmp = []
            for (lemma, part_of_speech), count in freqs.items():
                tmp.append(
                    WordFreqs(
                        year=year,
                        lemma=lemma,
                        frequency=count,
                        part_of_speech=part_of_speech
                    )
                )
            for slice in each_slice(tmp, 3000):
                WordFreqs.objects.bulk_create(slice)

    @database_sync_to_async
    def clean(self):
        Word.objects.all().delete()

    @database_sync_to_async
    def select_years(self):
        return sorted([item['year'] for item in WordFreqs.objects.values('year').distinct()], reverse=True)

    @database_sync_to_async
    def select_top_for_year(self, year, top, black_list):
        return list(WordFreqs.objects.filter(year=year).exclude(lemma__in=black_list).order_by('-frequency')[:top].values())

    @database_sync_to_async
    def load_black_list(self):
        blacklist = list(Lists.objects.filter(black_or_white='black').values())
        return list(sorted(blacklist, key=lambda item: max([int(x) for x in item['frequencies'].split(',')]), reverse=True))

    @database_sync_to_async
    def load_white_list(self):
        return set([word.lemma for word in Lists.objects.filter(black_or_white='white')])

    async def load_top_by_years(self):
        top = int(await get('top'))
        top_by_years = []

        black_list = await self.load_black_list()
        black_list_words = [item['lemma'] for item in black_list]
        years = sorted(list(set([int(item['year']) for item in json.loads(await get('year_to_source_files'))])), reverse=True)

        weight_factors = json.loads(await get('weight_factors', '{}'))
        white_list = await self.load_white_list()
        for year in years:
            words = await self.select_top_for_year(year, top, black_list_words)
            for word in words:
                word['in_whitelist'] = word['lemma'] in white_list
            top_by_years.append({
                'year': year,
                'words': words,
                'weight_factor': weight_factors.get(str(year), 4)
            })

        await self.send_msg({
            'fn': 'update',
            'value': {
                'black_list': black_list,
                'top_by_years': top_by_years,
                'year_to_source_files': json.loads(await get('year_to_source_files')),
                'included_parts_of_speech': json.loads(await get('included_parts_of_speech'))
            }
        })

    async def extract_words(self, _):
        folder_with_pdfs = await get('folder_with_pdfs')
        nlp = spacy.load("en_core_web_md")
        await self.clean()
        for file in os.listdir(folder_with_pdfs):
            if not file.endswith('.pdf'):
                continue

            path = os.path.join(folder_with_pdfs, file)
            doc = pymupdf.open(path)
            for page in doc:
                text = page.get_text()
                await self.extract_words_from_text(text, file, nlp)

        year_to_source_files = json.loads(await get('year_to_source_files'))
        await self.count_freqs(year_to_source_files)

        included_parts_of_speech = json.loads(await get('included_parts_of_speech'))
        await self.update_included_parts_of_speech_sync(included_parts_of_speech)
        await self.load_top_by_years()

    async def calc_created_at(self, _):
        folder_with_pdfs = await get('folder_with_pdfs')
        year_to_source_files = []

        for file in os.listdir(folder_with_pdfs):
            if not file.endswith('.pdf'):
                continue

            path = os.path.join(folder_with_pdfs, file)
            created_at = datetime.fromtimestamp(os.path.getctime(path))
            year_to_source_files.append({
                'year': created_at.year,
                'file': file
            })

        year_to_source_files_as_json = json.dumps(year_to_source_files)
        await update('year_to_source_files', year_to_source_files_as_json)
        await self.send_msg({
            'fn': 'update',
            'value': {
                'year_to_source_files': year_to_source_files_as_json,
            }
        })

    async def update_year(self, params):
        await update('year_to_source_files', params['value'])

    @database_sync_to_async
    def load_words(self):
        return list(WordFreqs.objects.all())

    @database_sync_to_async
    def update_included_parts_of_speech_sync(self, included_parts_of_speech):
        all_pos = ['PROPN', 'NOUN', 'ADJ', 'VERB', 'ADP', 'DET', 'SCONJ', 'AUX', 'PART', 'ADV', 'PRON', 'CCONJ', 'NUM', 'INTJ', 'X', 'SYM']

        excluded_pos = set(all_pos) - set(included_parts_of_speech)

        whitelisted = set([item.lemma for item in Lists.objects.filter(
            black_or_white='white',
            set_by='manual'
        )])
        blacklisted = set([item.lemma for item in Lists.objects.filter(
            black_or_white='black',
            set_by='manual'
        )])
        words_to_exclude = {}
        for word in WordFreqs.objects.all():
            if word.lemma in blacklisted:
                words_to_exclude.setdefault(word.lemma, []).append(str(word.frequency))
            elif word.part_of_speech in excluded_pos and word.lemma not in whitelisted:
                words_to_exclude.setdefault(word.lemma, []).append(str(word.frequency))

        Lists.objects.filter(black_or_white='black').exclude(set_by='manual').delete()
        tmp = [Lists(black_or_white='black', set_by='pos', lemma=lemma, frequencies=','.join(frequencies)) for lemma, frequencies in words_to_exclude.items()]
        Lists.objects.bulk_create(tmp)

    async def update_included_parts_of_speech(self, params):
        await update('included_parts_of_speech', params['value'])
        await self.update_included_parts_of_speech_sync(json.loads(params['value']))
        await self.load_top_by_years()

    @database_sync_to_async
    def add_to_blacklist_sync(self, params):
        word = WordFreqs.objects.filter(id=params['id']).first()
        Lists.objects.filter(lemma=word.lemma).delete()
        freqs = ','.join([str(word.frequency) for word in WordFreqs.objects.filter(lemma=word.lemma)])
        Lists(
            lemma=word.lemma,
            black_or_white='black',
            set_by='manual',
            frequencies=freqs
        ).save()

    async def add_to_blacklist(self, params):
        await self.add_to_blacklist_sync(params)
        await self.load_top_by_years()

    @database_sync_to_async
    def add_to_whitelist_sync(self, params):
        word = Lists.objects.filter(id=params['id']).first()
        Lists.objects.filter(lemma=word.lemma).delete()
        Lists(
            lemma=word.lemma,
            black_or_white='white',
            set_by='manual'
        ).save()

    async def add_to_whitelist(self, params):
        await self.add_to_whitelist_sync(params)
        await self.load_top_by_years()

