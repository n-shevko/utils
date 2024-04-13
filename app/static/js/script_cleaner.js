script_cleaner = {
  data: {
    progress: 0,
    progressMsg: null,
    inProgress: false,
    taskId: null
  },
  watch: {
    'state.script_cleaner_model': {
      handler(newValue, oldValue) {
        if (newValue === 'chat_gpt') {
          this.state.script_cleaner_algorithm = 'not_whole_context';
        }
      }
    }
  },
  methods: {
    runChatgpt(answer) {
      if (answer) {
        if (!this.validPlaceholders()) {
          return
        }
        this.sendMessage({fn: 'run_chatgpt', answer: true, delimeter: this.delimeter});
        this.hideModal();
      } else {
        this.unlockRun();
      }
    },
    unlockRun() {
      this.inProgress = false;
      this.hideModal();
    },
    copyResult() {
      navigator.clipboard.writeText(this.state.script_cleaner_last_answer_gpt);
    },
    script_cleaner_run() {
      if (this.validPlaceholders()) {
        this.inProgress = true;
        this.sendMessage({fn: 'script_cleaner_run'})
      }
    },
    stopScriptCleaner() {
      this.sendMessage({fn: 'update', key: `stop_${this.taskId}`, value: '1'});
      this.inProgress = false;
    },
    runClaude3(answer) {
      if (answer) {
        this.sendMessage({fn: 'run_claude', answer: true, delimeter: this.delimeter});
        this.hideModal();
      } else {
        this.unlockRun();
      }
    },
    validPlaceholders(){
      let valid;
      if (this.state.script_cleaner_algorithm === 'not_whole_context') {
        valid = this.state.script_cleaner_prompt_not_whole_context.indexOf('{chunk}') !== -1;
        if (!valid) {
          alert('Use {chunk} in your prompt');
        }
      } else {
        valid = this.state.script_cleaner_prompt_whole_context.indexOf('{all_chunks}') !== -1 && this.state.script_cleaner_prompt_whole_context.indexOf('{chunk_number}') !== -1
        if (!valid) {
          alert('Use {all_chunks} and {chunk_number} in your prompt');
        }
      }
      return valid;
    }
  },
  computed: {
    script_cleaner_last_answer_gpt() {
      if (this.state.script_cleaner_last_answer_gpt === undefined) {
        return '';
      } else {
        return this.state.script_cleaner_last_answer_gpt.replace(/\n/g, '<br>');
      }
    },
    script_cleaner_prompt: {
      get() {
        return this.state.script_cleaner_algorithm === 'not_whole_context' ? this.state.script_cleaner_prompt_not_whole_context : this.state.script_cleaner_prompt_whole_context;
      },
      set(value) {
        if (this.state.script_cleaner_algorithm === 'not_whole_context') {
          this.state.script_cleaner_prompt_not_whole_context = value;
        } else {
          this.state.script_cleaner_prompt_whole_context = value;
        }
      }
    }
  }
};