import pytest

from continuityos.crypto import ZKPProver, ZKPReserveProof


def test_zkp_reserve_proof_valid() -> None:
    # Organization has 60 days of fuel.
    prover = ZKPProver(actual_reserve=60, max_capacity=1000)

    # Generate public commitment
    commitment = prover.generate_commitment(
        entity_id="nato-logistics-1", commodity_id="F-76-Diesel"
    )

    assert commitment.max_capacity == 1000
    assert commitment.commitment_hash_hex

    # Prove that we have at least 45 days
    proof = prover.prove_minimum(required_minimum=45)

    # Assert fields
    assert proof.policy_minimum == 45
    assert proof.commitment_hash_hex == commitment.commitment_hash_hex

    # Verifier checks the proof
    assert proof.verify(max_capacity=1000) is True


def test_zkp_reserve_proof_invalid_minimum() -> None:
    prover = ZKPProver(actual_reserve=20, max_capacity=1000)

    # Try to prove we have 30 days when we only have 20.
    # The prover logic correctly raises an exception preventing false proof generation.
    with pytest.raises(ValueError, match="actual reserve is below required minimum"):
        prover.prove_minimum(required_minimum=30)


def test_zkp_reserve_proof_tampered() -> None:
    prover = ZKPProver(actual_reserve=50, max_capacity=1000)
    proof = prover.prove_minimum(required_minimum=30)

    # Tamper with the proof by using a different hash
    tampered_proof = ZKPReserveProof(
        commitment_hash_hex=proof.commitment_hash_hex,
        policy_minimum=30,
        proof_hash_hex="deadbeef" * 8,
    )

    assert tampered_proof.verify(max_capacity=1000) is False

    # Tamper by claiming a higher minimum than what was actually proven (e.g. proof was for 30, claiming 40)
    tampered_proof2 = ZKPReserveProof(
        commitment_hash_hex=proof.commitment_hash_hex,
        policy_minimum=40,
        proof_hash_hex=proof.proof_hash_hex,
    )

    assert tampered_proof2.verify(max_capacity=1000) is False
