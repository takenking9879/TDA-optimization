# Consolidation tables (this hardware: 4 CPU, 16 GB)

Ripser is 1 thread. PITH may use up to 4 threads for a few scans.
giotto-ph was not installed. GUDHI Rips ran only at n=200 (circle 0.085 s).

## Exact VR wall time
| family | n | T | dim | PITH exact (s) | Ripser (s) | ratio | pipeline |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| circle_noisy | 200 | 1.5 | 1 | 0.009 | 0.017 | 1.87× | pith:threshold+collapse-1+implicit_coh |
| circle_noisy | 500 | 1.5 | 1 | 0.018 | 0.302 | 16.96× | pith:auto-collapse |
| circle_noisy | 1000 | 1.5 | 1 | 0.072 | 2.216 | 30.85× | pith:auto-collapse |
| figure8 | 200 | 1.1 | 1 | 0.003 | 0.006 | 2.32× | pith:threshold+collapse-1+implicit_coh |
| figure8 | 500 | 1.1 | 1 | 0.010 | 0.031 | 3.20× | pith:auto-collapse |
| figure8 | 1000 | 1.1 | 1 | 0.026 | 0.162 | 6.20× | pith:auto-redzed-spatial |
| figure8 | 2000 | 1.1 | 1 | 0.150 | 2.528 | 16.85× | pith:auto-redzed-spatial |
| uniform2 | 500 | 0.35 | 1 | 0.011 | 0.021 | 1.92× | pith:auto-redzed |
| uniform2 | 1000 | 0.35 | 1 | 0.024 | 0.080 | 3.37× | pith:auto-redzed |
| uniform2 | 2000 | 0.35 | 1 | 0.056 | 0.436 | 7.81× | pith:auto-redzed |
| blobs | 1000 | 1.0 | 0 | 0.003 | 0.029 | 9.17× | pith:auto-redzed-h0-delaunay |
| blobs | 4000 | 1.0 | 0 | 0.009 | 0.556 | 62.11× | pith:auto-redzed-h0-delaunay |
| blobs | 12000 | 1.0 | 0 | 0.026 | 5.630 | 215.37× | pith:auto-redzed-h0-delaunay |
| sphere | 200 | 1.4 | 2 | 0.005 | 0.125 | 26.18× | pith:threshold+collapse-1+implicit_coh |
| sphere | 400 | 1.4 | 2 | 0.017 | 1.027 | 60.77× | pith:auto-collapse |
| circle_T | 400 | 0.6 | 1 | 0.007 | 0.012 | 1.77× | pith:auto-redzed-spatial |
| circle_T | 400 | 1.0 | 1 | 0.009 | 0.033 | 3.78× | pith:auto-collapse |
| circle_T | 400 | 1.5 | 1 | 0.012 | 0.120 | 9.88× | pith:auto-collapse |
| many_loops | 400 | 1.2 | 1 | 0.004 | 0.005 | 1.32× | pith:auto-redzed-cc |
| nested_loops | 400 | 1.6 | 1 | 0.011 | 0.046 | 4.27× | pith:auto-redzed |
| clustered | 400 | 0.8 | 1 | 0.003 | 0.005 | 1.58× | pith:auto-redzed-cc |
| heavy_noise_circle | 400 | 1.5 | 1 | 0.015 | 0.024 | 1.59× | pith:auto-collapse |
| anisotropic_blob | 400 | 2.5 | 1 | 0.009 | 0.015 | 1.62× | pith:auto-redzed-cc |
| torus | 400 | 1.6 | 1 | 0.010 | 0.026 | 2.66× | pith:auto-redzed-spatial |
| torus | 1000 | 1.6 | 1 | 0.043 | 0.393 | 9.11× | pith:auto-redzed-spatial |

## Scale path
| family | n | PITH scale (s) | |E| | ess H1 | ess H2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| figure8 | 200 | 0.004 | 3283 | 2 | 0 |
| figure8 | 500 | 0.007 | 12451 | 2 | 0 |
| figure8 | 1000 | 0.016 | 32842 | 2 | 0 |
| figure8 | 2000 | 0.034 | 79853 | 2 | 0 |
| sphere | 200 | 0.004 | 954 | 0 | 1 |
| sphere | 400 | 0.006 | 1934 | 0 | 1 |
| sphere | 4000 | 0.090 | 20122 | 0 | 1 |
| sphere | 16000 | 0.197 | 80641 | 0 | 1 |
| sphere | 50000 | 0.664 | 252311 | 0 | 1 |
| figure8 | 8000 | 0.220 | 428139 | 2 | 0 |
| figure8 | 16000 | 0.505 | 877739 | 2 | 0 |
| many_loops | 400 | 0.005 | 5143 | 5 | 0 |
| nested_loops | 400 | 0.007 | 11299 | 1 | 0 |
| heavy_noise_circle | 400 | 0.006 | 12405 | 0 | 0 |

## Topology at n=400 vs Ripser
| family | exact match | exact unmatched | scale unmatched | ess exact | ess Ripser | ess scale |
| --- | --- | ---: | ---: | --- | --- | --- |
| figure8 | True | 0 | 0 | H1=2 H2=0 | H1=2 H2=0 | H1=2 H2=0 |
| circle_noisy | True | 0 | 0 | H1=1 H2=0 | H1=1 H2=0 | H1=1 H2=0 |
| sphere | True | 0 | 52 | H1=0 H2=1 | H1=0 H2=1 | H1=0 H2=1 |

## Dispatcher (same 250-pt probe as `--engine auto`)

This check is **not** an independent oracle: `--estimate` and `--engine auto`
share the residual-frac / edge-frac probe, so agreement is expected.
It still catches implementation drift. Held-out families were not used
to set τ.
| family | recommended | picked | agree | exact feasible | wall (s) |
| --- | --- | --- | --- | --- | ---: |
| many_loops | redzed | redzed | True | True | 0.004 |
| nested_loops | redzed | redzed | True | True | 0.014 |
| clustered | redzed | redzed | True | True | 0.003 |
| heavy_noise_circle | implicit | implicit | True | True | 0.022 |
| figure8 | implicit | implicit | True | True | 0.009 |
| circle_noisy | implicit | implicit | True | True | 0.017 |

## Local time exponents (empirical slopes, not theorems)
| family | method | n0 | n1 | p_time | p_edges |
| --- | --- | ---: | ---: | ---: | ---: |
| circle_noisy | pith_exact | 200 | 500 | 0.77 | 2.00 |
| circle_noisy | pith_exact | 500 | 1000 | 2.01 | 2.00 |
| circle_noisy | ripser | 200 | 500 | 3.17 |  |
| circle_noisy | ripser | 500 | 1000 | 2.87 |  |
| figure8 | pith_exact | 200 | 500 | 1.49 | 2.00 |
| figure8 | pith_exact | 500 | 1000 | 1.42 | -0.01 |
| figure8 | pith_exact | 1000 | 2000 | 2.52 | 1.96 |
| figure8 | ripser | 200 | 500 | 1.84 |  |
| figure8 | ripser | 500 | 1000 | 2.37 |  |
| figure8 | ripser | 1000 | 2000 | 3.96 |  |
| figure8 | pith_scale | 200 | 500 | 0.71 | 1.45 |
| figure8 | pith_scale | 500 | 1000 | 1.10 | 1.40 |
| figure8 | pith_scale | 1000 | 2000 | 1.14 | 1.28 |
| figure8 | pith_scale | 2000 | 8000 | 1.34 | 1.21 |
| figure8 | pith_scale | 8000 | 16000 | 1.20 | 1.04 |
| uniform2 | pith_exact | 500 | 1000 | 1.10 | 2.00 |
| uniform2 | pith_exact | 1000 | 2000 | 1.23 | 2.00 |
| uniform2 | ripser | 500 | 1000 | 1.91 |  |
| uniform2 | ripser | 1000 | 2000 | 2.44 |  |
| blobs | pith_exact | 1000 | 4000 | 0.74 | 1.01 |
| blobs | pith_exact | 4000 | 12000 | 0.98 | 1.00 |
| blobs | ripser | 1000 | 4000 | 2.12 |  |
| blobs | ripser | 4000 | 12000 | 2.11 |  |
| sphere | pith_exact | 200 | 400 | 1.82 | 2.00 |
| sphere | ripser | 200 | 400 | 3.03 |  |
| sphere | pith_scale | 200 | 400 | 0.55 | 1.02 |
| sphere | pith_scale | 400 | 4000 | 1.20 | 1.02 |
| sphere | pith_scale | 4000 | 16000 | 0.56 | 1.00 |
| sphere | pith_scale | 16000 | 50000 | 1.07 | 1.00 |
| torus | pith_exact | 400 | 1000 | 1.63 | 2.00 |
| torus | ripser | 400 | 1000 | 2.98 |  |
