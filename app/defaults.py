defaults = {
    'margin_revisions_acceptor': {
        'docx_to_accept_revisions': '',
        'last_result_accept_revisions': ''
    },
    'script_cleaner': {
        'selected_video': '',

        'script_cleaner_prompt_not_whole_context': '''{chunk}

Convert the text above to standard English.''',
        'script_cleaner_prompt_whole_context': '''{all_chunks}

Convert the text from chunk number {chunk_number} to standard English. 
Don't shorten the text.''',
        
        'use_existing_files': '1',
        'percent_of_max_tokens_to_use_for_response': '50',

        'script_cleaner_last_out_file': '',
        'script_cleaner_last_answer_gpt': '',

        'script_cleaner_model': 'chat_gpt',
        'script_cleaner_algorithm': 'not_whole_context',
        'claude_max_tokens': '2046'
    },
    'citations_recovering': {
        'docx_with_broken_citations': '',
        'docx_with_normal_citations': '',
        'last_docx_result': ''
    },
    'text_image_feedback_spiral': {
        'text_image_feedback_spiral_chat_gpt_max_tokens': '1000',
        'dall_e_prompt': 'Draw 3 circles',
        'dall_e_model': 'dall-e-3',
        'dall_e_size': '1024x1024',
        'dall_e_quality': 'standard',
        'dall_e_n': '1',
        'suggest_changes_prompt': 'What do you think it is better change in this image? Make your suggestions as prompt'
                                  ' to dalle 3. Provide only suggestions as not numbered list and without '
                                  'any other text.'
    }
}
