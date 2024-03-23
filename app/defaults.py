defaults = {
    'script_cleaner': {
        'selected_video': '',
        'script_cleaner_prompt': 'You will be provided with statements, and your task is to convert them to standard English.',
        'use_existing_files': '1',
        'percent_of_max_tokens_to_use_for_response': '50',

        'script_cleaner_last_out_file': '',
        'script_cleaner_last_answer_gpt': ''
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
