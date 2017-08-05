pragma solidity ^0.4.4;

contract DelayContract {
    address beneficiaryAddress;
    uint value;
    uint activationTime;
    
    event DemandEvent(uint timestamp);
    
    modifier onlyAfterActivation() {
        DemandEvent(block.timestamp);
        require(block.timestamp >= activationTime);
        _;
    }
    
    modifier onlyBeneficiary() {
        require(msg.sender == beneficiaryAddress);
        _;
    }
    
    
    /// @dev Contract constructor sets initial beneficiary addresses and activation timestamp.
    /// @param _beneficiaryAddress address of beneficiary.
    /// @param _activationTime activation timestamp.
    function DelayContract(address _beneficiaryAddress, uint _activationTime)
        public
        payable
    {
        require(msg.value > 0);
        activationTime = _activationTime;
        beneficiaryAddress = _beneficiaryAddress;
        value = msg.value; 
    }
    
    
    /// @dev Сarry out the transaction if current timestamp more or equal activation timestamp.
    function demandTransaction() 
        onlyAfterActivation
        onlyBeneficiary
        public
    {
        beneficiaryAddress.send(value);
    }
}