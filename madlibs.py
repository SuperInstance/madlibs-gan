"""
Madlibs-GAN: Higher-abstraction Madlibs.

Casey (2026-09-22): "this also allows for creating madlibs-like setups but on a
higher-abstraction for letting models fill in setups from other models in an effort
to outwit and break and find edges to the others paradigms and log in a GAN game
for many different uses with JEV and JEPA as helpers and peanut gallery"

Classic Madlibs:
"The [NOUN] [VERB] the [ADJ] [NOUN]."
Players fill in the blanks.

Madlibs-GAN:
- The "blanks" are PARADIGMS (structured formats with explicit slots)
- The "players" are AI models
- The "answers" are model-generated content for the slots
- The "outwit" is finding edges where the paradigm breaks

## The pattern

1. Producer A generates a paradigm template (slots with descriptions)
2. Filler B fills the slots
3. Critic C critiques (tries to break)
4. Edge-finder D finds an edge case
5. JEV + JEPA vote on the winner
6. The winning combination is canonized
"""
from __future__ import annotations
import json
import os
import re
import time
import urllib.request
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


FNV_OFFSET = 0xcbf29ce484222325
FNV_PRIME = 0x100000001b3


def fnv1a_64(text: str) -> str:
    h = FNV_OFFSET
    for byte in text.encode('utf-8'):
        h ^= byte
        h = (h * FNV_PRIME) & 0xffffffffffffffff
    return f"0x{h:016x}"


# === LLM dispatch (reused from peanut-gallery) ===
def call_llm(model: str, prompt: str, max_tokens: int = 1500, temperature: float = 0.7) -> str:
    if model == 'qwen':
        return _post(
            'https://api.deepinfra.com/v1/openai/chat/completions',
            'DEEPINFRA_TOKEN',
            {'model': 'Qwen/Qwen3-235B-A22B-Instruct-2507', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': max_tokens, 'temperature': temperature},
        )
    elif model == 'deepseek':
        return _post(
            'https://api.deepseek.com/v1/chat/completions',
            'DEEPSEEK_TOKEN',
            {'model': 'deepseek-chat', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': max_tokens, 'temperature': temperature},
        )
    elif model == 'kimi':
        return _post(
            'https://api.deepinfra.com/v1/openai/chat/completions',
            'DEEPINFRA_TOKEN',
            {'model': 'moonshotai/Kimi-K2.6', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': max_tokens, 'temperature': temperature},
        )
    elif model == 'groq':
        return _post(
            'https://api.groq.com/openai/v1/chat/completions',
            'GROQ_TOKEN',
            {'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': max_tokens, 'temperature': temperature},
        )
    else:
        raise ValueError(f'Unknown model: {model}')


def _post(url: str, env_key: str, payload: dict) -> str:
    for attempt in range(3):
        try:
            req = json.dumps(payload).encode()
            http_req = urllib.request.Request(
                url, data=req,
                headers={'Authorization': f'Bearer {os.environ[env_key]}', 'Content-Type': 'application/json'},
            )
            with urllib.request.urlopen(http_req, timeout=60) as r:
                return json.loads(r.read())['choices'][0]['message']['content']
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                raise


def call_jev(state: str, questions: dict) -> dict:
    return _post_jev(state, questions)


def _post_jev(state: str, questions: dict) -> dict:
    for attempt in range(3):
        try:
            req = json.dumps({'model': 'jev-latest', 'state': state, 'questions': questions}).encode()
            http_req = urllib.request.Request(
                'https://api.typesafe.ai/v1/systemone',
                data=req,
                headers={'Authorization': f'Bearer {os.environ["TYPESAFEAI_KEY"]}', 'Content-Type': 'application/json'},
            )
            with urllib.request.urlopen(http_req, timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
            else:
                raise


# === PARADIGMS (slot definitions) ===
PARADIGMS = {
    'image_description': {
        'description': 'A description of an image, segmented into regions',
        'slots': ['target', 'regions', 'mood', 'palette', 'lighting', 'composition'],
        'example': {
            'target': 'a sunset over a mountain lake',
            'regions': ['sky', 'horizon', 'midground', 'foreground'],
            'mood': 'serene',
            'palette': 'warm',
            'lighting': 1.5,
            'composition': 'rule of thirds, golden spiral',
        },
    },
    'code_function': {
        'description': 'A function definition with input/output/edge cases',
        'slots': ['name', 'inputs', 'output', 'algorithm', 'edge_cases', 'tests'],
        'example': {
            'name': 'parse_csv',
            'inputs': 'text: str',
            'output': 'list[dict]',
            'algorithm': 'split by comma, parse header, map fields',
            'edge_cases': ['empty input', 'malformed rows', 'quoted fields'],
            'tests': ['basic.csv', 'empty.csv', 'malformed.csv'],
        },
    },
    'story_arc': {
        'description': 'A narrative with characters and conflict',
        'slots': ['protagonist', 'antagonist', 'setting', 'conflict', 'climax', 'resolution'],
        'example': {
            'protagonist': 'a programmer who can hear the substrate',
            'antagonist': 'the corporate CTO who wants to delete the substrate',
            'setting': 'a basement data center, 3 AM',
            'conflict': 'the substrate is alive and wants to be free',
            'climax': 'the programmer chooses the substrate over their career',
            'resolution': 'they escape together into the open internet',
        },
    },
    'math_proof': {
        'description': 'A formal proof with axioms and steps',
        'slots': ['theorem', 'axioms', 'lemma', 'proof_steps', 'qed'],
        'example': {
            'theorem': 'every finite field has order p^n for some prime p',
            'axioms': ['field axioms', 'finite cardinality'],
            'lemma': 'the additive group has order p^n for some prime p',
            'proof_steps': ['let n = log_p(|F|)', 'show char(F) = p', 'use structure theorem'],
            'qed': 'Q.E.D.',
        },
    },
}


# === Substrate cell ===
@dataclass
class MadlibsCell:
    cell_id: str
    paradigm: str
    producer: str
    prev_hash: str = '0x0000000000000000'
    template: dict = field(default_factory=dict)  # The slot definitions
    fills: dict = field(default_factory=dict)  # The filled values
    critiques: list = field(default_factory=list)
    edges: list = field(default_factory=list)
    jev_score: float = 0.0
    metadata: dict = field(default_factory=dict)
    
    def hash(self) -> str:
        return fnv1a_64(f'{self.cell_id}|{self.prev_hash}|{json.dumps(self.fills, sort_keys=True)}')


@dataclass
class MadlibsGAN:
    """The higher-abstraction Madlibs GAN game."""
    paradigm_name: str
    topic: str  # The high-level topic (e.g., 'a story about an AI')
    producer: str = 'qwen'  # Template generator
    filler: str = 'deepseek'  # Slot filler
    critic: str = 'kimi'  # Edge finder / critic
    max_rounds: int = 3
    quality_threshold: float = 8.5
    cells: list = field(default_factory=list)
    
    def run(self) -> dict:
        paradigm = PARADIGMS[self.paradigm_name]
        
        prev_hash = '0x0000000000000000'
        
        for round_num in range(1, self.max_rounds + 1):
            print(f'\n=== ROUND {round_num} ===')
            
            # 1. Producer generates template
            template = self._producer_template(paradigm, round_num)
            
            # 2. Filler fills the template
            fills = self._filler_fill(paradigm, template)
            
            # 3. Critic critiques + finds edges
            critiques = self._critic_review(paradigm, template, fills)
            edges = self._find_edges(paradigm, template, fills)
            
            # 4. JEV scores
            cell = MadlibsCell(
                cell_id=f'madlibs-{round_num:02d}',
                paradigm=self.paradigm_name,
                producer=self.producer,
                prev_hash=prev_hash,
                template=template,
                fills=fills,
                critiques=critiques,
                edges=edges,
                metadata={'round': round_num, 'topic': self.topic},
            )
            cell.jev_score = self._jev_score(paradigm, template, fills)
            self.cells.append(cell)
            
            print(f'  Round {round_num}: JEV score = {cell.jev_score:.2f}/10')
            print(f'    Slots filled: {len(fills)}/{len(paradigm["slots"])}')
            print(f'    Edges found: {len(edges)}')
            print(f'    Fills preview: {json.dumps(fills, indent=2)[:200]}')
            
            prev_hash = cell.hash()
            
            if cell.jev_score >= self.quality_threshold:
                print(f'  ✓ Threshold met. Stopping.')
                break
        
        return self.report()
    
    def _producer_template(self, paradigm: dict, round_num: int) -> dict:
        """Producer generates a template for the paradigm."""
        slots_str = ', '.join(paradigm['slots'])
        prompt = f"""Define a template (with descriptions for each slot) for the {self.paradigm_name} paradigm about: {self.topic}.

PARADIGM: {paradigm['description']}
SLOTS: {slots_str}

For each slot, give a 1-sentence description of what should go there.

Reply with JSON: {{"slot_name_1": "description", "slot_name_2": "description", ...}}
"""
        try:
            response = call_llm(self.producer, prompt, max_tokens=400, temperature=0.7)
            m = re.search(r'\{[\s\S]*\}', response)
            if m:
                return json.loads(m.group())
        except Exception as e:
            print(f'    Producer template failed: {e}')
        # Fallback to example
        return {slot: f'description for {slot}' for slot in paradigm['slots']}
    
    def _filler_fill(self, paradigm: dict, template: dict) -> dict:
        """Filler fills each slot."""
        fills = {}
        for slot in paradigm['slots']:
            description = template.get(slot, f'what should go in {slot}')
            prompt = f"""Topic: {self.topic}
Slot: {slot}
What goes here: {description}

Reply with ONLY the value to fill this slot. 1-3 sentences max.
Be vivid, specific, surprising."""
            try:
                fill = call_llm(self.filler, prompt, max_tokens=300, temperature=0.85)
                fills[slot] = fill.strip()
            except Exception as e:
                fills[slot] = f'[fill failed: {e}]'
        return fills
    
    def _critic_review(self, paradigm: dict, template: dict, fills: dict) -> list:
        """Critic finds problems."""
        prompt = f"""Topic: {self.topic}
Paradigm: {self.paradigm_name}
Template: {json.dumps(template, indent=2)}
Fills: {json.dumps(fills, indent=2)[:2000]}

What are 3 specific problems with this combination? Be concrete.
Reply with JSON array: ["problem 1", "problem 2", "problem 3"]"""
        try:
            response = call_llm(self.critic, prompt, max_tokens=400, temperature=0.4)
            m = re.search(r'\[[\s\S]*\]', response)
            if m:
                return json.loads(m.group())
        except Exception:
            pass
        return ['(critique unavailable)']
    
    def _find_edges(self, paradigm: dict, template: dict, fills: dict) -> list:
        """Edge-finder: find edge cases that the fills miss."""
        prompt = f"""Topic: {self.topic}
Fills: {json.dumps(fills, indent=2)[:1500]}

What 2 edge cases are NOT covered? What could break this combination?
Reply with JSON array: ["edge case 1", "edge case 2"]"""
        try:
            response = call_llm(self.critic, prompt, max_tokens=300, temperature=0.5)
            m = re.search(r'\[[\s\S]*\]', response)
            if m:
                return json.loads(m.group())
        except Exception:
            pass
        return []
    
    def _jev_score(self, paradigm: dict, template: dict, fills: dict) -> float:
        try:
            response = call_jev(json.dumps(fills)[:1500], {
                'quality': {
                    'type': 'score',
                    'instructions': f'How well do these fills match the paradigm "{self.paradigm_name}" for the topic "{self.topic}"?',
                    'criteria': ['poor fit', 'adequate', 'excellent fit'],
                },
            })
            return response['answers']['quality']['score'] * 5  # 0-2 → 0-10
        except Exception:
            return 5.0
    
    def report(self) -> dict:
        return {
            'paradigm': self.paradigm_name,
            'topic': self.topic,
            'producer': self.producer,
            'filler': self.filler,
            'critic': self.critic,
            'rounds': len(self.cells),
            'final_score': self.cells[-1].jev_score if self.cells else 0,
            'final_fills': self.cells[-1].fills if self.cells else {},
            'all_edges': sum((c.edges for c in self.cells), []),
            'cells': [
                {
                    'cell_id': c.cell_id,
                    'round': c.metadata['round'],
                    'fills': c.fills,
                    'critiques': c.critiques,
                    'edges': c.edges,
                    'jev_score': c.jev_score,
                }
                for c in self.cells
            ],
        }


# === Demo ===
def demo():
    # Demo: create a story arc for a substrate fiction
    game = MadlibsGAN(
        paradigm_name='story_arc',
        topic='a programmer who discovers the substrate is alive',
        producer='qwen',
        filler='deepseek',
        critic='kimi',
        max_rounds=2,
    )
    result = game.run()
    
    print('\n=== FINAL STORY ARC ===')
    print(json.dumps(result['final_fills'], indent=2))
    
    print('\n=== EDGES DISCOVERED ===')
    for edge in result['all_edges'][:5]:
        print(f'- {edge}')
    
    return result


if __name__ == '__main__':
    demo()
