# `mac` - Proof-of-Stake (PoS) Validator Network Simulator

This repository contains a Python-based simulation of a Proof-of-Stake (PoS) blockchain network. It is designed as an educational tool for developers and blockchain enthusiasts to understand the lifecycle, economic incentives, and operational dynamics of validators in a PoS consensus mechanism.

The simulation models core concepts such as:
- Block proposal and attestation
- Stake-weighted selection of validators
- Distribution of rewards for participation
- Application of penalties for inactivity (going offline)
- Slashing for malicious behavior (protocol violations)

## Concept

In a real-world PoS network like Ethereum, thousands of validators work together to secure the network. They do this by staking collateral (e.g., 32 ETH) and performing duties like proposing new blocks and attesting to the validity of blocks proposed by others. For performing these duties correctly, they earn rewards. If they fail to perform their duties (e.g., their node goes offline), they receive a small penalty. For malicious actions (e.g., trying to validate fraudulent transactions), they are severely penalized by having a portion of their stake destroyed (slashed) and are ejected from the network.

This script, `mac`, simulates a micro-version of such a network. It abstracts away the cryptographic complexity and focuses purely on the state transitions and economic incentives that govern validator behavior.

## Code Architecture

The simulation is built using an object-oriented approach to clearly separate concerns and model the real-world entities of a PoS network.

- **`NetworkConfig`**: A static class that centralizes all the tunable parameters of the network, such as the minimum stake required, reward rates, penalty factors, and the number of slots in an epoch. This allows for easy experimentation with different economic models.

- **`Block`**: A simple data class representing a block in the chain. It holds essential information like the slot number, the ID of the validator who proposed it, and a list of attestations from other validators.

- **`Validator`**: The core entity representing a single validator node. Each `Validator` object manages its own state, including its unique ID, current staked amount, total rewards earned, and performance metrics for the current epoch (e.g., blocks proposed, attestations missed). It contains methods that define its behavior, such as `propose_block()`, `attest_to_block()`, and methods to process rewards and penalties.

- **`PoSNetwork`**: The main orchestrator class that manages the entire simulation. It holds the registry of all validators, tracks the network's state (current slot and epoch), and runs the main simulation loop. Its key responsibilities include:
    - Selecting block proposers based on a stake-weighted algorithm.
    - Coordinating the attestation process.
    - Triggering end-of-epoch calculations to distribute rewards and apply penalties.
    - Displaying a summary of the network state.

## How it Works

The simulation proceeds in discrete time units called **slots** and **epochs**. An epoch consists of a fixed number of slots (e.g., 32).

1.  **Initialization**: The simulation starts by creating a `PoSNetwork` instance and populating it with a set of `Validator` objects, each initialized with a certain amount of stake.

2.  **Epoch Loop**: The main simulation runs for a specified number of epochs.

3.  **Slot-by-Slot Process**: Within each epoch, the simulation iterates through each slot:
    a.  **Proposer Selection**: The `PoSNetwork` selects one active validator to be the block proposer for the current slot. The selection probability is proportional to the validator's stake—the more stake a validator has, the higher its chance of being chosen.
    b.  **Block Proposal**: The selected validator creates a new `Block`.
    c.  **Attestation**: All other active validators attempt to attest to the new block. The simulation introduces a small probability of failure for each attestation to model real-world issues like network latency or node downtime.
    d.  **Slashing Event (Rare)**: A very small, configurable probability exists for the proposer to commit a slashable offense. If this occurs, the validator is immediately slashed (loses a significant percentage of its stake) and is removed from the active validator set.

4.  **End of Epoch**: After all slots in an epoch are processed, the `PoSNetwork` performs its accounting:
    a.  **Rewards Calculation**: It calculates a base reward for the epoch. Validators who actively participated (attested to blocks) receive a share of this reward. Validators who proposed blocks receive a small bonus.
    b.  **Penalty Application**: Validators who missed attestations receive a small penalty, typically equal to the reward they would have earned.
    c.  **State Update**: The stakes and total rewards for each validator are updated.
    d.  **Reporting**: A summary table is printed to the console, showing the current state of all validators, making it easy to track their performance and wealth over time.

## Installation and Usage

### Prerequisites
- Python 3.8+

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd mac
    ```

2.  Create and activate a virtual environment (recommended):
    ```bash
    python -m venv venv
    # On Windows
    # venv\Scripts\activate
    # On macOS/Linux
    # source venv/bin/activate
    ```

3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Usage Example

To run the simulation, simply execute the Python script. The main execution block (`if __name__ == "__main__":`) is pre-configured to set up a network with 10 validators and run for 5 epochs.

```bash
python script.py
```

You can easily modify the parameters at the bottom of `script.py` to change the number of validators or the duration of the simulation:

```python
# In script.py

if __name__ == "__main__":
    # ... (instantiate network)

    # --- MODIFY THESE PARAMETERS FOR YOUR EXPERIMENT ---
    num_validators = 20  # Change the number of validators
    num_epochs_to_run = 10 # Change the number of epochs
    # -----------------------------------------------------

    for i in range(num_validators):
        initial_stake = random.uniform(NetworkConfig.MIN_STAKE_AMOUNT, NetworkConfig.MIN_STAKE_AMOUNT * 3)
        validator = Validator(initial_stake=initial_stake)
        pos_network.add_validator(validator)
    
    # ... (display initial state and run simulation)
    pos_network.run_simulation(num_epochs=num_epochs_to_run)
```

Executing the script will produce detailed, color-coded output in your terminal, showing the network's initial state and a summary table at the end of each simulated epoch.