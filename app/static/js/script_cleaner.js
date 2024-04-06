script_cleaner = {
  data: {
    progress: 0,
    progressMsg: null,
    inProgress: false,
    taskId: null
  },
  methods: {
    runChatgpt(answer) {
      if (answer) {
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
      this.inProgress = true;
      this.sendMessage({fn: 'script_cleaner_run'})
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
    }
  },
  computed: {
    script_cleaner_last_answer_gpt() {
      return this.state.script_cleaner_last_answer_gpt.replace(/\n/g, '<br>');
    },
    script_cleaner_prompt: {
      get() {
        return this.state.script_cleaner_model === 'chat_gpt' ? this.state.script_cleaner_prompt_chat_gpt : this.state.script_cleaner_prompt_claude_3;
      },
      set(value) {
        if (this.state.script_cleaner_model === 'chat_gpt') {
          this.state.script_cleaner_prompt_chat_gpt = value;
        } else {
          this.state.script_cleaner_prompt_claude_3 = value;
        }
      }
    }
  }
};