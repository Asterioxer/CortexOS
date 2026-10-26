# Blockchain, Smart Contracts & Web3 Workspace

- **Primary Locations**: 
  - `C:\Users\soham\Desktop\blockchain` (Cryptographic foundations & Bitcoin scripts)
  - `C:\Users\soham\Desktop\Solidity` (EVM smart contracts)
  - `C:\Users\soham\Desktop\Token_ERC721` & `Token_ERC1155` (NFTs & Multi-tokens)
  - `C:\Users\soham\Desktop\BLC_TheFracture` (Decentralized game stack)
- **Primary Toolchains**: Solidity (`solc`), Python 3 (`hashlib`, `ecdsa`), Node.js, Web3.js / Ethers.js, Remix IDE, Docker Compose

## Core Subsystems
1. **Cryptographic Proofs & Mining**:
   - `bitcoin_miner.py`: Python implementation of SHA-256 Proof-of-Work difficulty target hashing and block generation.
   - `bitcoin_real.py`: Base58Check address derivation, public key hashing (RIPEMD160), and raw transaction serialization.
   - `blockchain_cryptography_foundations.ipynb`: Interactive Jupyter notebooks deriving elliptic curve mathematics (secp256k1) and Merkle tree generation.
2. **Smart Contract Architectures**:
   - Standard ERC-20, ERC-721 (NFT), and ERC-1155 (Multi-token) implementations.
   - State-machine game contracts (`Rock_Paper_Scissors_BLC`, `RPS_Game`) with commit-reveal schemes preventing front-running on public mempools.

## Safety & Governance Guidelines
Smart contract compilation and deployment scripts must adhere to strict Cedar policy:
- No private key strings or mnemonics may be stored in plaintext within source code.
- Always utilize `.env` files protected by `.gitignore` and system environment variables.

---
## Related Notes
- [[Cedar_Security_Governance]]
- [[Toolchains_and_Compilers]]
- [[Filesystem_and_Workspaces]]
