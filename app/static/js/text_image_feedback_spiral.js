text_image_feedback_spiral = {
  data: {
    last_steps: []
  },
  methods: {
    text_image_feedback_spiral() {
      this.sendMessage({fn: 'get_feedback_spiral_context'});
    },
    step() {
      this.inProgress = true;
      this.progress = 0;
      this.sendMessage({fn: 'step'});
    },
    setInprogressFalse(){
      this.inProgress = false;
    }
  }
}