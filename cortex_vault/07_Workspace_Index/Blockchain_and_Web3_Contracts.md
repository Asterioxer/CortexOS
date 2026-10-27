---
title: "Blockchain, Smart Contracts & Web3 Workspace"
type: "workspace_catalog"
tags:
  - cortex/workspaces
  - cortex/blockchain
  - cortex/solidity
  - cortex/web3
  - cortex/smart_contracts
last_updated: "2026-10-27"
status: "verified"
---

# ⛓️ Blockchain, Smart Contracts & Web3 Workspace

- **Primary Locations**: 
  - `C:\Users\soham\Desktop\blockchain` (Cryptographic foundations, Merkle roots & Bitcoin scripts)
  - `C:\Users\soham\Desktop\Solidity` (EVM smart contracts & Remix artifacts)
  - `C:\Users\soham\Desktop\Token_BLC` & `Token_N` (ERC-20 tokens, banking & Web3 interfaces)
  - `C:\Users\soham\Desktop\Token_ERC721` & `Token_ERC1155` (NFTs, Game Inventories & Quiz games)
  - `C:\Users\soham\Desktop\Rock_Paper_Scissors_BLC`, `rps-project` & `RPS_Game` (On-chain gaming & NFT rewards)
  - `C:\Users\soham\Desktop\BLC_TheFracture` (Decentralized game stack with Docker Compose)
- **Primary Toolchains**: Solidity (`solc`), Python 3 (`hashlib`, `ecdsa`), Node.js, Web3.js, Ethers.js, Remix IDE, Hardhat / Vite

## 🏛️ Comprehensive Repository & Contract Map

### 1. Cryptographic Proofs & Bitcoin Mechanics (`C:\Users\soham\Desktop\blockchain`)
- `bitcoin_miner.py`: Python implementation of SHA-256 Proof-of-Work difficulty target hashing and block nonce mining.
- `bitcoin_real.py`: Base58Check address derivation, public key hashing (RIPEMD160 / SHA256), and raw transaction serialization.
- `new_btc_merkel_root.py`: Computes cryptographic Merkle trees from transaction hash leaves to derive the block header root.
- `blockchain_cryptography_foundations.ipynb`: Interactive Jupyter notebook deriving elliptic curve mathematics (secp256k1) and signature verification.
- `dApp/` & `DApp_SecA/`: Minimal decentralized applications interacting with MetaMask via `etherjs.html` and `myscr.js`.

---

### 2. EVM Smart Contracts Catalog (`C:\Users\soham\Desktop\Solidity\contracts`)
- `StudentDetails.sol` & `studroll.sol`: Storage mapping patterns, struct arrays, and access-controlled record management.
- `bankAcc.sol` & `makepayment.sol`: Safe payable functions, balance tracking, and reentrancy defense patterns.
- `ArithmeticOperations.sol`, `calculator.sol`, `SquareNumber.sol`: Pure math operations, overflow checks, and EVM gas profiling.
- `artifacts/`: Compiled ABI definitions and bytecode targets compiled for Ethereum `cancun` and `prague` hard-fork VMs.

---

### 3. Token Standards Implementation
- **ERC-20 Tokens (`Token_BLC` & `Token_N`)**:
  - `Token_BLC/contracts/MyToken.sol`: OpenZeppelin-based standard fungible token with minting and allowance capabilities.
  - `Token_BLC/ui/scadila-ui`: React client frontend providing wallet connection and token transfer UI.
  - `Token_N/contracts/TokenRKA.sol` & `TokenSNS.sol`: Specialized custom tokens.
  - `Token_N/contracts/banking.sol`: Decentralized deposit and loan management contract (`GECBANK`).
- **ERC-721 Non-Fungible Tokens (`Token_ERC721`)**:
  - `contracts/Meth01.sol` & `Meth02.sol`: Unique token ID minting, ownership registries, and metadata URI mapping.
- **ERC-1155 Multi-Tokens (`Token_ERC1155`)**:
  - `contracts/game_inventory.sol`: Batch minting of semi-fungible and non-fungible items for game itemization.
  - `contracts/QuizGame.sol` & `QuizGame1.sol`: Interactive on-chain quiz rewarding correct answers with unique token badges.

---

### 4. Decentralized Gaming & Commit-Reveal Engines
- **`Rock_Paper_Scissors_BLC` & `RPS_Game`**:
  - `RockPaperScissorsNFT.sol`: Minting commemorative trophy NFTs to winners upon match completion.
  - Interactive web UI (`index.html`, `style.css`, `script.js`) connecting to web3 providers.
- **`rps-project`**:
  - `RockPaperScissorsReward.sol`: Smart contract managing wager pools and token distributions.
  - `rps-backend/server.js`: Node.js Express arbitration backend verifying match cooldowns (`cooldowns.json`) and audit logs (`logs.js`).
  - `WALLET_REWARDS_GUIDE.md`: Comprehensive walkthrough for player wallet integration and prize claiming.
- **`BLC_TheFracture`**:
  - Full game architecture documented in `THE_FRACTURE_GDD_AND_PROMPT.md` (51 KB Game Design Document).
  - Orchestrated via `docker-compose.yml`.

---

## 🛡️ Safety & Cedar Governance Guidelines
Smart contract compilation and deployment scripts must adhere to strict Cedar policy:
- No private key strings or mnemonics may ever be committed in plaintext or logged.
- All deployments must reference `.env` keys protected by `.gitignore`.
- Automated testing in Remix or local Hardhat nodes before mainnet or testnet deployment.

---
## Related Notes
- [[07_Workspace_Index/Desktop_Workspace_Master_Index|Desktop Workspace Master Index]]
- [[01_Architecture/Governance_Cedar|Cedar Security Governance]]
- [[05_System_State/Toolchains_and_Compilers|Toolchains and Compilers]]
- [[05_System_State/Filesystem_and_Workspaces|Filesystem and Workspaces]]
