var RouterFabric = artifacts.require("RouterFabric.sol");

module.exports = function(deployer) {
  // deployment steps
  deployer.deploy(RouterFabric);
};