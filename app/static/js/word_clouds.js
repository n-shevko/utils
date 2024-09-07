word_clouds = {
  data: {
    yearToWords: [],
    year_to_source_files: [],
    top_by_years: [],
    black_list: [],
    included_parts_of_speech: [],
    parts_of_speech: [
      { pos: 'PROPN', label: 'Proper Noun' },
      { pos: 'NOUN', label: 'Noun' },
      { pos: 'ADJ', label: 'Adjective' },
      { pos: 'VERB', label: 'Verb' },
      { pos: 'ADP', label: 'Adposition' },
      { pos: 'DET', label: 'Determiner' },
      { pos: 'SCONJ', label: 'Subordinating Conjunction' },
      { pos: 'AUX', label: 'Auxiliary Verb' },
      { pos: 'PART', label: 'Particle' },
      { pos: 'ADV', label: 'Adverb' },
      { pos: 'PRON', label: 'Pronoun' },
      { pos: 'CCONJ', label: 'Coordinating Conjunction' },
      { pos: 'NUM', label: 'Numeral' },
      { pos: 'INTJ', label: 'Interjection' },
      { pos: 'X', label: 'Other' },
      { pos: 'SYM', label: 'Symbol' }
    ],
    years_config: {},
    inProgress: false,
  },
  watch: {
    year_to_source_files(newVal) {
      if (typeof(newVal) === 'string') {
        this.year_to_source_files = JSON.parse(newVal);
      }
    },
    top_by_years() {
      this.inProgress = false;
    }
  },
  methods: {
    preview(year) {
      let self = this;
      this.top_by_years.map(function (item) {
        if (year === undefined || item.year === year) {
          let list = item.words.map(function (word) {
            return [word.lemma, word.frequency];
          });

          WordCloud(document.getElementById(item.year),
            {
              list: list,
              weightFactor: function (size) {
                return size * item.weight_factor;
              },
              fontFamily: 'Times, serif',
              color: 'random-dark',
              rotateRatio: 0.5,
              rotationSteps: 2,
              backgroundColor: self.state.background_color
            });
        }
      })
    },
    word_clouds() {
      this.sendMessage({fn: 'word_clouds_context'});
    },
    topChanged() {
      this.inProgress = true;
      this.sendMessage({fn: 'word_clouds_context'});
    },
    extract_words() {
      this.inProgress = true;
      this.sendMessage({fn: 'extract_words'});
    },
    showCreatedAt() {
      this.inProgress = true;
      this.sendMessage({fn: 'calc_created_at'});
    },
    updateYear() {
      if (!this.year_to_source_files.every( i => String(i.year).length === 4)) {
        return
      }
      this.inProgress = true;
      this.sendMessage({
        fn: 'update_year',
        value: JSON.stringify(this.year_to_source_files)
      });
    },
    addToBlacklist(word) {
      this.sendMessage({fn: 'add_to_blacklist', id: word.id});
    },
    addToWhitelist(word) {
      this.sendMessage({fn: 'add_to_whitelist', id: word.id});
    },
    parts_of_speech_updated() {
      this.sendMessage(
        {
          fn: 'update_included_parts_of_speech',
          value: JSON.stringify(this.included_parts_of_speech)}
      )
      this.inProgress = true;
    },
    updateWeightFactors(year) {
      let weight_factors = {}
      this.top_by_years.map(function (i) {
        weight_factors[i.year] = i.weight_factor;
      })
      this.sendMessage(
        {
          fn: 'update',
          key: 'weight_factors',
          value: JSON.stringify(weight_factors)}
      )
      this.preview(year);
    },
    generateVideo() {
      let body = this.top_by_years.map(function (item) {
        const canvas = document.getElementById(item.year);
        return {image: canvas.toDataURL("image/png"), year: item.year}
      })
      let self = this;
      this.inProgress = true;
      fetch('/save_png', {
          method: 'POST',
          body: JSON.stringify(body),
          headers: {
              'Content-Type': 'application/json',
          }
      }).then(response => response.json())
        .then(data => {
          self.inProgress = false;
          if (data.out === undefined) {
            alert("Somethig went wrong")
          } else {
            alert(`Result file ${data.out}`)
            self.state.words_video = data.out;
          }
        })
    }
  }
}