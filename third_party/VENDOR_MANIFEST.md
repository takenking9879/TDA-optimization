# External repository manifest

Pinned, unmodified snapshots used as baselines. Do not edit files under
`third_party/` except this manifest and the `UPSTREAM_COMMIT` stamp.

| Name | URL | License | Commit | Local path | Purpose |
| --- | --- | --- | --- | --- | --- |
| Ripser | https://github.com/Ripser/ripser | MIT | `01add51ff64aaf40889483260cc5c3b7d0f2a1e7` | `third_party/ripser/` | Exact VR CPU baseline (implicit cohomology) |
| Ripser++ | https://github.com/simonzhang00/ripser-plusplus | MIT | `30243c0c752de26d7fdf6e41f08bf7b840ca4744` | `third_party/ripser-plusplus/` | GPU reference only. **Local clone, not a remote fork.** |
| RedZeD | https://github.com/nkershaw01/RedZeD | MIT | `22ef1bf8696bccad02b041a83863d12d4bd92766` | `third_party/redzed/` | Exact VR engine (active enumeration). PITH `--engine redzed` (I228). |

## Ripser++ status in this environment

- Cloned 2026-10-13. Upstream left unmodified.
- No NVIDIA GPU / `nvidia-smi` / `nvcc` in the Cloud Agent image.
- **Not compiled. No GPU timings are claimed.**
- This is a local working-tree clone. A GitHub fork was not created
  (no write permission to the user's GitHub assumed; keep upstream URL).

## Not vendored

| Name | Reason |
| --- | --- |
| giotto-ph | AGPL-3. Use as an optional pip oracle only; do not copy source. |
| GUDHI | MIT, but large. Optional system/pip oracle for collapse and Alpha. I227: flag collapse is slower than PITH on n=2000. |
| redzed-tda (PyPI) | MIT wheel used as I227 oracle. In-tree copy is `third_party/redzed/` (same upstream). |
| Oineus | LBNL BSD + grant-back. Independent reference, not a kernel. |
| Ripserer.jl | MIT, Julia not installed here. |

## How to rebuild Ripser

```sh
c++ -std=c++11 -O3 -DNDEBUG third_party/ripser/ripser.cpp -o third_party/ripser/ripser
```
