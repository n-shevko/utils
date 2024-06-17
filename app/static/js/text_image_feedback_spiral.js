text_image_feedback_spiral = {
  data: {
    last_steps: [],
    spiralInProgress: false,
    spiralProgress: 0
  },
  methods: {
    text_image_feedback_spiral() {
      this.sendMessage({fn: 'get_feedback_spiral_context'});
    },
    step() {
      this.spiralInProgress = true;
      this.spiralProgress = 0;
      this.sendMessage({fn: 'step'});
    },
    setInprogressFalse(){
      this.spiralInProgress = false;
    }
  }
}