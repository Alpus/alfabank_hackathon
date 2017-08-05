module.exports = {
    build: {
      "constants.js": [
        "migrations/constants.js"
      ],
    },
    rpc: {
        host: "localhost",
        port: 8545
    },
    networks: {
        development: {
            // host: "34.208.247.57",
            host: "localhost",
            port: 8545,
            network_id: "*"
        }
    }
};

