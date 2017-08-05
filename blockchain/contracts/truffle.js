module.exports = {
    build: {
      "constants.js": [
        "migrations/constants.js"
      ],
    },
    rpc: {
        host: "34.208.247.57",
        port: 8485
    },
    networks: {
        development: {
            host: "34.208.247.57",
            port: 8485,
            network_id: "*"
        }
    }
};

