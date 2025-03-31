import random
import time
import uuid
from typing import List, Dict, Optional, Tuple

from faker import Faker
from rich.console import Console
from rich.table import Table

# Initialize external libraries
faker = Faker()
console = Console()

class NetworkConfig:
    """
    A configuration class to hold all network parameters.
    This makes the simulation easily tunable and parameters are centralized.
    """
    SLOTS_PER_EPOCH: int = 32
    MIN_STAKE_AMOUNT: float = 32.0
    BASE_REWARD_PER_EPOCH: float = 0.0001  # A base reward factor
    INACTIVITY_PENALTY_FACTOR: float = 0.5  # Penalty is a fraction of the base reward
    SLASHING_PENALTY_PERCENTAGE: float = 0.05  # 5% of stake is slashed for severe offenses
    PROPOSER_BONUS_FACTOR: float = 0.1 # Proposer gets a small bonus (10% of the reward)
    
    # Simulation-specific parameters
    VALIDATOR_ONLINE_PROBABILITY: float = 0.98 # Chance a validator is online to attest
    SLASHABLE_OFFENSE_PROBABILITY: float = 0.001 # Very low chance of a slashable offense

class Block:
    """
    Represents a single block in the blockchain.
    In this simulation, it's a simplified data structure to track proposals and attestations.
    """
    def __init__(self, slot_number: int, proposer_id: str):
        self.slot_number = slot_number
        self.proposer_id = proposer_id
        self.attestations: List[str] = []
        self.timestamp = time.time()

    def add_attestation(self, validator_id: str):
        """Adds a validator's attestation to the block."""
        if validator_id not in self.attestations:
            self.attestations.append(validator_id)

class Validator:
    """
    Represents a single validator node in the Proof-of-Stake network.
    Manages its own state, including stake, rewards, and performance metrics.
    """
    def __init__(self, initial_stake: float):
        if initial_stake < NetworkConfig.MIN_STAKE_AMOUNT:
            raise ValueError(f"Initial stake must be at least {NetworkConfig.MIN_STAKE_AMOUNT}")

        self.id: str = str(uuid.uuid4())
        self.name: str = f"validator-{faker.word()}-{self.id[:4]}"
        self.staked_amount: float = initial_stake
        self.rewards_earned: float = 0.0
        self.is_active: bool = True

        # Performance tracking for an epoch
        self.slots_attested: int = 0
        self.slots_missed: int = 0
        self.proposed_blocks: int = 0

    def __repr__(self) -> str:
        return f"Validator(id={self.id}, stake={self.staked_amount:.4f}, active={self.is_active})"

    def propose_block(self, slot_number: int) -> Block:
        """Action: Propose a new block for a given slot."""
        console.log(f"[bold cyan]Validator {self.name}[/] is proposing a block for slot {slot_number}.")
        self.proposed_blocks += 1
        return Block(slot_number, self.id)

    def attest_to_block(self) -> bool:
        """
        Action: Attest to a block. Simulates network latency or node downtime.
        Returns True if the validator successfully attests, False otherwise.
        """
        if random.random() < NetworkConfig.VALIDATOR_ONLINE_PROBABILITY:
            self.slots_attested += 1
            return True
        else:
            self.slots_missed += 1
            return False

    def process_epoch_rewards(self, reward: float, is_proposer_bonus: bool = False):
        """Updates the validator's balance with earned rewards."""
        self.staked_amount += reward
        self.rewards_earned += reward
        bonus_text = "(Proposer Bonus)" if is_proposer_bonus else ""
        #console.log(f"Validator {self.name} received reward of {reward:.6f} ETH. {bonus_text}")

    def process_inactivity_penalty(self, penalty: float):
        """Applies a penalty for being offline (missing attestations)."""
        self.staked_amount -= penalty
        self.rewards_earned -= penalty
        #console.log(f"[yellow]Validator {self.name} penalized by {penalty:.6f} ETH for inactivity.[/yellow]")

    def process_slashing(self):
        """
        Applies a severe penalty for a major protocol violation.
        The validator is forcefully exited from the active set.
        """
        slashed_amount = self.staked_amount * NetworkConfig.SLASHING_PENALTY_PERCENTAGE
        self.staked_amount -= slashed_amount
        self.is_active = False
        console.log(f"[bold red]CRITICAL: Validator {self.name} SLASHED! Lost {slashed_amount:.4f} ETH and ejected from the network.[/bold red]")

    def reset_epoch_metrics(self):
        """Resets performance counters at the start of a new epoch."""
        self.slots_attested = 0
        self.slots_missed = 0
        self.proposed_blocks = 0


class PoSNetwork:
    """
    Orchestrates the entire Proof-of-Stake simulation.
    Manages the set of validators, the blockchain state (slots, epochs),
    and the application of consensus rules, rewards, and penalties.
    """
    def __init__(self):
        self.validators: Dict[str, Validator] = {}
        self.current_slot: int = 0
        self.current_epoch: int = 0
        self.chain: List[Block] = []

    def add_validator(self, validator: Validator):
        """Registers a new validator into the network's pool."""
        if validator.id in self.validators:
            console.log(f"[bold red]Error:[/] Validator with ID {validator.id} already exists.")
            return
        self.validators[validator.id] = validator
        console.log(f"Validator {validator.name} with {validator.staked_amount:.2f} ETH joined the network.")

    def _get_active_validators(self) -> List[Validator]:
        """Returns a list of all validators that are currently active."""
        return [v for v in self.validators.values() if v.is_active]

    def _select_block_proposer(self) -> Optional[Validator]:
        """
        Selects a block proposer for the current slot.
        The selection is weighted by the validator's staked amount. Higher stake means
        a higher chance of being selected, which is a core tenet of PoS.
        """
        active_validators = self._get_active_validators()
        if not active_validators:
            return None

        total_stake = sum(v.staked_amount for v in active_validators)
        weights = [v.staked_amount / total_stake for v in active_validators]

        # Weighted random selection
        proposer = random.choices(active_validators, weights=weights, k=1)[0]
        return proposer

    def _process_epoch_end(self):
        """
        Handles the logic at the end of an epoch:
        1. Calculate the base reward for this epoch.
        2. Distribute rewards to active attesters.
        3. Apply penalties to inactive validators.
        4. Reset validator metrics for the next epoch.
        """
        console.log(f"\n[bold magenta]>>>> Epoch {self.current_epoch} finished. Processing rewards and penalties... <<<<[/bold magenta]")
        active_validators = self._get_active_validators()
        if not active_validators:
            return

        total_active_stake = sum(v.staked_amount for v in active_validators)
        
        # The total reward pool scales with the amount of stake participating
        epoch_reward_pool = total_active_stake * NetworkConfig.BASE_REWARD_PER_EPOCH
        base_reward_per_validator = epoch_reward_pool / len(active_validators) 
        
        for validator in active_validators:
            # Reward for attesting
            if validator.slots_attested > 0:
                # Reward is proportional to participation
                participation_rate = validator.slots_attested / (validator.slots_attested + validator.slots_missed)
                reward = base_reward_per_validator * participation_rate
                validator.process_epoch_rewards(reward)

            # Penalty for inactivity
            if validator.slots_missed > 0:
                penalty = base_reward_per_validator * NetworkConfig.INACTIVITY_PENALTY_FACTOR
                validator.process_inactivity_penalty(penalty)
            
            # Bonus for proposing a block
            if validator.proposed_blocks > 0:
                proposer_bonus = base_reward_per_validator * NetworkConfig.PROPOSER_BONUS_FACTOR * validator.proposed_blocks
                validator.process_epoch_rewards(proposer_bonus, is_proposer_bonus=True)

            validator.reset_epoch_metrics()

        self.display_validator_status()

    def display_validator_status(self):
        """Prints a summary table of all validators' current status."""
        table = Table(title=f"Network Status at End of Epoch {self.current_epoch}")
        table.add_column("Validator Name", style="cyan", no_wrap=True)
        table.add_column("ID", style="dim")
        table.add_column("Status", justify="center")
        table.add_column("Stake (ETH)", justify="right", style="green")
        table.add_column("Total Rewards (ETH)", justify="right", style="yellow")

        for validator in sorted(self.validators.values(), key=lambda v: v.staked_amount, reverse=True):
            status = "[green]Active[/green]" if validator.is_active else "[red]Slashed[/red]"
            table.add_row(
                validator.name,
                validator.id,
                status,
                f"{validator.staked_amount:.4f}",
                f"{validator.rewards_earned:.6f}"
            )
        console.print(table)

    def run_simulation(self, num_epochs: int):
        """Main simulation loop."""
        console.log(f"[bold green]Starting PoS Network Simulation for {num_epochs} epochs.[/bold green]")
        
        for epoch in range(num_epochs):
            self.current_epoch = epoch
            console.log(f"\n[bold blue]--- Starting Epoch {self.current_epoch} ---[/bold blue]")
            
            for _ in range(NetworkConfig.SLOTS_PER_EPOCH):
                self.current_slot += 1
                #console.log(f"-- Slot {self.current_slot} --")

                # 1. Select a proposer for the current slot
                proposer = self._select_block_proposer()
                if not proposer:
                    console.log("[bold red]No active validators to propose a block. Halting simulation.[/bold red]")
                    return

                # 2. Proposer creates a block
                new_block = proposer.propose_block(self.current_slot)
                
                # 3. Simulate a rare slashable offense (e.g., double-voting)
                if random.random() < NetworkConfig.SLASHABLE_OFFENSE_PROBABILITY:
                    proposer.process_slashing()
                    # If slashed, the proposed block is invalid
                    continue 

                # 4. Other validators attest to the new block
                attesting_validators = self._get_active_validators()
                for attester in attesting_validators:
                    if attester.id != proposer.id:
                        if attester.attest_to_block():
                            new_block.add_attestation(attester.id)

                self.chain.append(new_block)

            # 5. End of Epoch Processing
            self._process_epoch_end()
            time.sleep(1) # Pause for readability

        console.log("\n[bold green]Simulation finished.[/bold green]")


if __name__ == "__main__":
    # --- Simulation Setup ---
    # 1. Instantiate the network
    pos_network = PoSNetwork()

    # 2. Create and add validators with varying initial stakes
    num_validators = 10
    for i in range(num_validators):
        # Use a random stake to make the simulation more realistic
        initial_stake = random.uniform(NetworkConfig.MIN_STAKE_AMOUNT, NetworkConfig.MIN_STAKE_AMOUNT * 3)
        validator = Validator(initial_stake=initial_stake)
        pos_network.add_validator(validator)

    # Display initial state
    console.rule("[bold]Initial Network State[/bold]")
    pos_network.display_validator_status()
    console.rule()

    # 3. Run the simulation for a few epochs
    pos_network.run_simulation(num_epochs=5)
