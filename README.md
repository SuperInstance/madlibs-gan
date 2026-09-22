# madlibs-gan

> **MADLIBS on a higher abstraction.** Models fill in setups from other models in an effort to outwit, break, and find edges to each other's paradigms.

Classic Madlibs is: "The [NOUN] [VERB] the [ADJ] [NOUN]." Players fill in the blanks.

**MADLIBS-GAN is the same, but the players are AI models, and the blanks are PARADIGMS.**

## The pattern

1. Model A produces a setup with blanks (the "Madlib template")
2. Model B fills in the blanks (the "answer")
3. Model C critiques (the "gallery response")
4. Model D tries to outwit both A and B (the "edge")
5. JEV + JEPA vote on the winner
6. The winning combination becomes a new cell in the substrate

## What is a "paradigm"?

A paradigm is a structured format with explicit slots. Examples:
- An image description with regions (sky, horizon, midground, foreground)
- A code function with parameters (input, output, edge_cases, tests)
- A story with characters (protagonist, antagonist, conflict, resolution)
- A math proof with steps (axioms, lemma, theorem, qed)

Each paradigm is a substrate cell with multiple slots.

## The GAN game

Round 1: Model A generates a paradigm template.
Round 2: Model B fills it in.
Round 3: Model C critiques (tries to break it).
Round 4: Model D finds an edge case.
Round 5: JEV decides if the cycle continues or breaks.

The cycle breaks when:
- Quality ≥ 9.0
- All edge cases are covered
- JEV gives high confidence on convergence

## Use cases

- **Image description** (extends JEV-Diffusion)
- **Code generation** (extends motif-quilt)
- **Story writing** (extends text-diffusion)
- **Strategy** (game AI, multi-agent negotiations)
- **Math** (proof generation, theorem finding)

## Files (coming)

- `madlibs.py` — the template engine
- `paradigms.py` — paradigm definitions
- `round.py` — a single round of the GAN game
- `voting.py` — JEV + JEPA voting
- `examples/` — pre-run games
