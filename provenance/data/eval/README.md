# Held-out evaluation sets

Empty on purpose. These sets are the difference between a number you can defend
and a number you made up, and they must be built before there is anything to
evaluate — otherwise the threshold gets chosen to flatter the result.

`mlr/results/HARNESS_SELFTEST_NOT_A_BASELINE.txt` in this repository sets the
standard being followed here.

## What goes here

    similarity/
      plagiarism_pairs.jsonl    Known reuse. From the PAN plagiarism corpus.
      unrelated_pairs.jsonl     Same field, same vocabulary, no copying.
                                Measures false positives -- the harder number.

    aidetect/
      human_l1.jsonl            Pre-2020 human text. Cannot be contaminated by
                                instruction-tuned models, so it is a clean
                                negative.
      human_l2.jsonl            Second-language English writing. THE CONTROL SET.
                                The published false positive rate comes from
                                this file and nowhere else.
      machine.jsonl             Generated via detector.providers.Router.
      machine_adversarial.jsonl Paraphrased and edited machine text.

Record format, one JSON object per line:

    {"id": "...", "text": "...", "label": 0, "source": "...", "notes": "..."}

## Rules

1. **No number produced by `MockDetector` ever appears in a result file.** The
   mock fabricates plausible output; that is what it is for, and it is why every
   mock report carries `is_mock`.

2. **Report precision at a fixed 1% false positive rate**, never accuracy.
   Accuracy on an imbalanced set means nothing and flatters everything.

3. **The second-language control set is not optional.** A detector evaluated
   only on first-language English will look excellent and will wrongly flag the
   people this service is most likely to serve. See docs/AI_DETECTION.md.

4. **Build the control set before reading any results.** A threshold tuned after
   seeing the numbers is not an evaluation.

5. **Consent for anything from real students**, recorded, per document.
