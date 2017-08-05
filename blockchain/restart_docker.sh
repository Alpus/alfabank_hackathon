docker stop blockchain
docker rm blockchain
#docker run blockchain
#docker run -itd -p localhost:8545 --name blockchain blockchain:latest

docker run -itd -p 8545:8545 --name blockchain blockchain:latest

