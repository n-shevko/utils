margin_revisions_acceptor = {
  methods: {
    accept_revisions() {
      this.sendMessage({fn: 'accept_revisions'})
    }
  }
}