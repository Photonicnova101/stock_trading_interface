module.exports = {
    resolve: {
      fallback: {
        crypto: false,
        stream: false,
        util: false,
        path: false,
        buffer: false,
        http: false,
        https: false,
        url: false,
        assert: false,
        zlib: false,
        tls: false,
        net: false,
      },
    },
  };
  