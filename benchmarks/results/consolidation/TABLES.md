# Consolidation tables (this hardware: 4 CPU, 16 GB)

Ripser is 1 thread. Phase-2 PITH times use `--threads 1` unless noted.
giotto-ph 0.2.4 (AGPL oracle) and GUDHI 3.13.0 are compared at equal hardware in the phase-3 tables below.

## Exact VR wall time (phase 1, PITH may use 4 threads)
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

## Thread-fair exact VR (`--threads 1` vs hardware vs Ripser)
| family | n | PITH 1-thr (s) | PITH hw-thr (s) | Ripser 1-thr (s) | 1-thr ratio | hw-thr ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| figure8 | 1000 | 0.028 | 0.025 | 0.158 | 5.64× | 6.43× |
| circle_noisy | 1000 | 0.070 | 0.069 | 2.205 | 31.40× | 32.07× |
| uniform2 | 1000 | 0.019 | 0.023 | 0.080 | 4.32× | 3.42× |
| sphere | 400 | 0.017 | 0.017 | 1.021 | 60.42× | 61.50× |
| blobs | 4000 | 0.009 | 0.009 | 0.549 | 59.19× | 60.75× |

## Forced engines (1 thread)
| family | n | auto (s) | redzed (s) | implicit (s) | estimate | oracle | waste |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |
| figure8 | 1000 | 0.02449003199581057 | 0.02177737100282684 | 0.035075095991487615 | redzed | redzed | 1.0 |
| circle_noisy | 1000 | 0.07041454600403085 | 0.08397716499166563 | 0.06799374699767213 | implicit | implicit | 1.0 |
| uniform2 | 1000 | 0.018606023004394956 | 0.01597702300932724 | 0.04378108000673819 | redzed | redzed | 1.0 |
| torus | 1000 | 0.03993717300181743 | 0.03711949499847833 | 0.2773486849910114 | redzed | redzed | 1.0 |
| nested_loops | 400 | 0.008636797007056884 | 0.006663234991719946 | 0.008194766996894032 | redzed | redzed | 1.0 |
| many_loops | 400 | 0.003448286995990202 | 0.002861654997104779 | 0.003479876002529636 | redzed | redzed | 1.0 |
| heavy_noise_circle | 400 | 0.015418022987432778 | 0.00538561400026083 | 0.011405354991438799 | implicit | redzed | 2.117744604586669 |
| clustered | 400 | 0.003732375000254251 | 0.0024313960020663217 | 0.004315089012379758 | redzed | redzed | 1.0 |

## Scale path
| family | n | PITH scale (s) | |E| | ess H1 | ess H2 | RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| figure8 | 200 | 0.004 | 3283 | 2 | 0 | 5054464 |
| figure8 | 500 | 0.007 | 12451 | 2 | 0 | 6389760 |
| figure8 | 1000 | 0.016 | 32842 | 2 | 0 | 9437184 |
| figure8 | 2000 | 0.034 | 79853 | 2 | 0 | 15532032 |
| sphere | 200 | 0.004 | 954 | 0 | 1 | 5251072 |
| sphere | 400 | 0.006 | 1934 | 0 | 1 | 6422528 |
| sphere | 4000 | 0.090 | 20122 | 0 | 1 | 139632640 |
| sphere | 16000 | 0.197 | 80641 | 0 | 1 | 36597760 |
| sphere | 50000 | 0.664 | 252311 | 0 | 1 | 91725824 |
| figure8 | 8000 | 0.220 | 428139 | 2 | 0 | 61714432 |
| figure8 | 16000 | 0.505 | 877739 | 2 | 0 | 134148096 |
| many_loops | 400 | 0.005 | 5143 | 5 | 0 | 5308416 |
| nested_loops | 400 | 0.007 | 11299 | 1 | 0 | 6123520 |
| heavy_noise_circle | 400 | 0.006 | 12405 | 0 | 0 | 5951488 |
| figure8 | 4000 | 0.086 | 186241 | 2 | 0 | 28102656 |
| many_loops | 1000 | 0.011 | 21387 | 5 | 0 | 7647232 |
| many_loops | 2000 | 0.028 | 59415 | 5 | 0 | 12185600 |
| nested_loops | 1000 | 0.019 | 39235 | 1 | 0 | 10539008 |
| nested_loops | 2000 | 0.036 | 76154 | 1 | 0 | 15429632 |
| loops_with_bridges | 400 | 0.006 | 10464 | 2 | 0 | 5771264 |
| loops_with_bridges | 1000 | 0.015 | 37423 | 2 | 0 | 9605120 |
| multi_scale_loops | 400 | 0.005 | 8865 | 1 | 0 | 5722112 |
| multi_scale_loops | 1000 | 0.015 | 32421 | 1 | 0 | 8130560 |
| mixed_1d2d3d | 300 | 0.005 | 1032 | 1 | 0 | 5500928 |
| mixed_1d2d3d | 600 | 0.011 | 2160 | 1 | 0 | 8130560 |
| multi_cavities | 300 | 0.005 | 1342 | 0 | 3 | 5607424 |
| multi_cavities | 600 | 0.010 | 2855 | 0 | 3 | 8450048 |
| outliers_sphere | 400 | 0.006 | 1844 | 0 | 1 | 6209536 |
| figure8 | 24000 | 0.794 | 1262726 | 2 | 0 | 229126144 |
| sphere | 80000 | 1.076 | 403615 | 0 | 1 | 159600640 |

## Topology vs Ripser (phase 2, bottleneck/Wasserstein when GUDHI provides them)
| family | n | exact match | scale unmatched | scale bn H1 | scale W1 H1 | ess scale | ess sparse |
| --- | ---: | --- | ---: | ---: | ---: | --- | --- |
| figure8 | 400 | True | 0 | 5e-07 |  | H1=2 H2=0 | H1=2 H2=0 |
| circle_noisy | 400 | True | 0 | 4.6e-07 |  | H1=1 H2=0 | H1=1 H2=0 |
| sphere | 400 | True | 52 | 0.02404 |  | H1=0 H2=1 | H1=None H2=None |
| nested_loops | 400 | True | 0 | 5.1e-06 |  | H1=1 H2=0 | H1=1 H2=0 |
| many_loops | 400 | True | 0 | 4.8e-07 |  | H1=5 H2=0 | H1=5 H2=0 |
| loops_with_bridges | 400 | True | 0 | 5.1e-07 |  | H1=2 H2=0 | H1=2 H2=0 |
| heavy_noise_circle | 400 | True | 0 | 5.1e-07 |  | H1=0 H2=0 | H1=0 H2=0 |
| multi_scale_loops | 400 | True | 0 | 4.8e-07 |  | H1=1 H2=0 | H1=1 H2=0 |
| mixed_1d2d3d | 300 | None | 35 | 0.02969 |  | H1=1 H2=0 | H1=None H2=None |
| multi_cavities | 300 | True | 52 | 0.04121 |  | H1=0 H2=3 | H1=0 H2=3 |

## Dispatcher oracle (1-thread; wrong = estimate ≠ faster engine)
| family | n | recommended | auto | oracle | wrong | waste | regime |
| --- | ---: | --- | --- | --- | --- | ---: | --- |
| figure8 | 1000 | redzed | redzed | redzed | False | 1.0 | hollow |
| circle_noisy | 1000 | implicit | implicit | implicit | False | 1.0 | thin |
| uniform2 | 1000 | redzed | redzed | redzed | False | 1.0 | fat |
| torus | 1000 | redzed | redzed | redzed | False | 1.0 | hollow |
| nested_loops | 400 | redzed | redzed | redzed | False | 1.0 | fat |
| many_loops | 400 | redzed | redzed | redzed | False | 1.0 | hollow |
| heavy_noise_circle | 400 | implicit | implicit | redzed | True | 2.117744604586669 | thin |
| clustered | 400 | redzed | redzed | redzed | False | 1.0 | hollow |

## Practical limits under a 12 s budget
| family | dim | method | max n ok | wall (s) | first fail n |
| --- | ---: | --- | ---: | ---: | ---: |
| anisotropic_blob | 1 | pith_exact | 1000 | 0.020 | None |
| anisotropic_blob | 1 | ripser | 1000 | 0.097 | None |
| blobs | 0 | pith_exact | 25000 | 0.053 | None |
| blobs | 0 | ripser | 12000 | 5.630 | None |
| circle_T | 1 | pith_exact | 800 | 0.016 | None |
| circle_T | 1 | ripser | 800 | 0.128 | None |
| circle_noisy | 1 | pith_exact | 4000 | 2.191 | None |
| circle_noisy | 1 | ripser | 1000 | 2.216 | 2000 |
| clustered | 1 | pith_exact | 400 | 0.003 | None |
| clustered | 1 | ripser | 400 | 0.005 | None |
| figure8 | 1 | pith_exact | 4000 | 1.026 | None |
| figure8 | 1 | pith_redzed | 4000 | 1.054 | None |
| figure8 | 1 | pith_scale | 24000 | 0.794 | None |
| figure8 | 1 | ripser | 2000 | 2.528 | 4000 |
| heavy_noise_circle | 1 | pith_exact | 400 | 0.015 | None |
| heavy_noise_circle | 1 | pith_scale | 400 | 0.006 | None |
| heavy_noise_circle | 1 | ripser | 400 | 0.024 | None |
| loops_with_bridges | 1 | pith_exact | 1000 | 0.041 | None |
| loops_with_bridges | 1 | pith_scale | 1000 | 0.015 | None |
| loops_with_bridges | 1 | ripser | 1000 | 0.161 | None |
| many_loops | 1 | pith_exact | 2000 | 0.027 | None |
| many_loops | 1 | pith_scale | 2000 | 0.028 | None |
| many_loops | 1 | ripser | 2000 | 0.313 | None |
| mixed_1d2d3d | 2 | pith_exact | None |  | 300 |
| mixed_1d2d3d | 2 | pith_scale | 600 | 0.011 | None |
| mixed_1d2d3d | 2 | ripser | 600 | 1.110 | None |
| multi_cavities | 2 | pith_exact | 600 | 0.067 | None |
| multi_cavities | 2 | pith_scale | 600 | 0.010 | None |
| multi_cavities | 2 | ripser | 600 | 0.370 | None |
| multi_scale_loops | 1 | pith_exact | 1000 | 0.023 | None |
| multi_scale_loops | 1 | pith_scale | 1000 | 0.015 | None |
| multi_scale_loops | 1 | ripser | 1000 | 0.406 | None |
| near_degenerate | 1 | pith_exact | 1000 | 0.011 | None |
| near_degenerate | 1 | ripser | 1000 | 0.033 | None |
| nested_loops | 1 | pith_exact | 2000 | 0.295 | None |
| nested_loops | 1 | pith_scale | 2000 | 0.036 | None |
| nested_loops | 1 | ripser | 2000 | 6.436 | None |
| outliers_sphere | 2 | pith_exact | 400 | 0.015 | None |
| outliers_sphere | 2 | pith_scale | 400 | 0.006 | None |
| outliers_sphere | 2 | ripser | 400 | 1.323 | None |
| sphere | 2 | pith_exact | 800 | 0.057 | None |
| sphere | 2 | pith_scale | 80000 | 1.076 | None |
| sphere | 2 | ripser | 400 | 1.027 | 800 |
| torus | 1 | pith_exact | 2000 | 0.196 | None |
| torus | 1 | ripser | 2000 | 2.479 | None |
| uniform2 | 1 | pith_exact | 4000 | 0.243 | None |
| uniform2 | 1 | ripser | 4000 | 1.990 | None |

## Non-Euclidean L1 (exact engine only)
| n | PITH auto (s) | PITH redzed (s) | Ripser (s) | exact match |
| ---: | ---: | ---: | ---: | --- |
| 200 | 0.04181634899578057 | 0.005313154004397802 | 0.013901921003707685 | True |
| 400 | 0.03567516499606427 | 0.015805119997821748 | 0.06376458900922444 | True |

## Local time exponents (empirical slopes, not theorems)
| family | method | n0 | n1 | p_time | p_edges |
| --- | --- | ---: | ---: | ---: | ---: |
| figure8 | pith_sparse | 2000 | 4000 | 1.73 | 1.39 |
| figure8 | pith_scale | 2000 | 4000 | 1.26 | 1.18 |
| figure8 | pith_sparse | 4000 | 8000 | 1.98 | 1.34 |
| figure8 | pith_scale | 4000 | 8000 | 1.38 | 1.21 |
| figure8 | pith_sparse | 8000 | 12000 | 2.01 | 1.29 |
| figure8 | pith_scale | 8000 | 12000 | 1.24 | 1.04 |
| figure8 | pith_sparse | 12000 | 16000 | 2.00 | 1.26 |
| figure8 | pith_scale | 12000 | 16000 | 1.11 | 1.02 |
| figure8 | pith_sparse | 16000 | 24000 | 1.89 | 1.28 |
| figure8 | pith_scale | 16000 | 24000 | 1.22 | 0.95 |
| circle_noisy | pith_sparse | 2000 | 4000 | 1.79 | 1.33 |
| circle_noisy | pith_scale | 2000 | 4000 | 1.37 | 1.27 |
| circle_noisy | pith_sparse | 4000 | 8000 | 1.96 | 1.31 |
| circle_noisy | pith_scale | 4000 | 8000 | 1.34 | 1.11 |
| circle_noisy | pith_sparse | 8000 | 12000 | 1.68 | 1.25 |
| circle_noisy | pith_scale | 8000 | 12000 | 1.10 | 0.91 |
| nested_loops | pith_sparse | 2000 | 4000 | 1.51 | 1.41 |
| nested_loops | pith_scale | 2000 | 4000 | 1.02 | 1.05 |
| nested_loops | pith_sparse | 4000 | 8000 | 2.17 | 1.36 |
| nested_loops | pith_scale | 4000 | 8000 | 1.42 | 1.23 |
| disconnected_circles | pith_sparse | 2000 | 4000 | 1.66 | 1.36 |
| disconnected_circles | pith_scale | 2000 | 4000 | 1.30 | 1.29 |
| disconnected_circles | pith_sparse | 4000 | 8000 | 1.93 | 1.34 |
| disconnected_circles | pith_scale | 4000 | 8000 | 1.41 | 1.17 |
| uniform4 | pith_sparse | 400 | 800 | 1.44 | 1.54 |
| uniform4 | pith_sparse | 800 | 1600 | 1.91 | 1.51 |
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
| figure8 | exact_auto | 2000 | 4000 | 2.79 |  |
| figure8 | exact_redzed | 2000 | 4000 | 2.79 |  |
| figure8 | scale | 2000 | 4000 | 1.31 |  |
| figure8 | scale | 4000 | 24000 | 1.24 |  |
| circle_noisy | exact_auto | 2000 | 4000 | 2.70 |  |
| many_loops | exact_auto | 1000 | 2000 | 1.72 |  |
| many_loops | ripser | 1000 | 2000 | 2.80 |  |
| many_loops | scale | 1000 | 2000 | 1.30 |  |
| nested_loops | exact_auto | 1000 | 2000 | 2.98 |  |
| nested_loops | ripser | 1000 | 2000 | 3.55 |  |
| nested_loops | scale | 1000 | 2000 | 0.94 |  |
| loops_with_bridges | exact_auto | 400 | 1000 | 1.75 |  |
| loops_with_bridges | ripser | 400 | 1000 | 2.76 |  |
| loops_with_bridges | scale | 400 | 1000 | 1.06 |  |
| multi_scale_loops | exact_auto | 400 | 1000 | 1.44 |  |
| multi_scale_loops | ripser | 400 | 1000 | 3.09 |  |
| multi_scale_loops | scale | 400 | 1000 | 1.11 |  |
| near_degenerate | exact_auto | 400 | 1000 | 1.17 |  |
| near_degenerate | ripser | 400 | 1000 | 1.88 |  |
| mixed_1d2d3d | ripser | 300 | 600 | 3.12 |  |
| mixed_1d2d3d | scale | 300 | 600 | 1.06 |  |
| multi_cavities | exact_auto | 300 | 600 | 3.65 |  |
| multi_cavities | ripser | 300 | 600 | 3.16 |  |
| multi_cavities | scale | 300 | 600 | 1.06 |  |

## Phase-3 equal-hardware baselines (giotto-ph + GUDHI)
PITH `--threads 1`. Ripser 1 thread. giotto-ph `n_threads=1` and `n_threads=4` (no edge collapse unless noted). GUDHI Rips is explicit (1 thread). giotto-ph 0.2.4 is AGPLv3 — oracle only.
| family | n | T | dim | PITH 1-thr | Ripser | giotto t1 | giotto t4 | GUDHI Rips |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| circle_noisy | 200 | 1.5 | 1 | 0.005 | 0.015 | 0.022 | 0.036 | 0.082 |
| circle_noisy | 500 | 1.5 | 1 | 0.017 | 0.299 | 0.349 | 0.358 | 1.658 |
| circle_noisy | 1000 | 1.5 | 1 | 0.068 | 2.158 | 2.469 | 2.436 | timeout |
| figure8 | 500 | 1.1 | 1 | 0.010 | 0.031 | 0.041 | 0.052 | 0.335 |
| figure8 | 1000 | 1.1 | 1 | 0.023 | 0.157 | 0.192 | 0.148 | 3.154 |
| figure8 | 2000 | 1.1 | 1 | 0.152 | 2.513 | 2.810 | 2.782 | timeout |
| sphere | 200 | 1.4 | 2 | 0.007 | 0.125 | 0.142 | 0.090 | 1.191 |
| sphere | 400 | 1.4 | 2 | 0.017 | 1.020 | 1.119 | 0.620 | timeout |
| uniform2 | 500 | 0.35 | 1 | 0.008 | 0.022 | 0.030 | 0.039 | 0.398 |
| uniform2 | 1000 | 0.35 | 1 | 0.018 | 0.079 | 0.103 | 0.096 | 3.780 |
| nested_loops | 400 | 1.6 | 1 | 0.009 | 0.046 | 0.055 | 0.068 | 0.155 |
| nested_loops | 1000 | 1.6 | 1 | 0.037 | 0.544 | 0.626 | 0.607 | 3.169 |
| many_loops | 400 | 1.2 | 1 | 0.004 | 0.005 | 0.009 | 0.022 | 0.016 |
| torus | 400 | 1.6 | 1 | 0.009 | 0.025 | 0.034 | 0.043 | 0.137 |
| torus | 1000 | 1.6 | 1 | 0.040 | 0.381 | 0.461 | 0.417 | 2.848 |
| disconnected_circles | 400 | 1.5 | 1 | 0.008 | 0.028 | 0.036 | 0.049 | 0.173 |
| disconnected_circles | 1000 | 1.5 | 1 | 0.037 | 0.429 | 0.499 | 0.506 | 3.902 |
| random_geometric_sparse | 500 | 0.15 | 1 | 0.006 | 0.007 | 0.012 | 0.023 | 0.017 |
| random_geometric_sparse | 1000 | 0.15 | 1 | 0.009 | 0.023 | 0.031 | 0.037 | 0.143 |
| random_geometric_dense | 400 | 0.5 | 1 | 0.009 | 0.020 | 0.030 | 0.039 | 0.644 |
| random_geometric_dense | 800 | 0.5 | 1 | 0.018 | 0.089 | 0.119 | 0.107 | 6.443 |
| grid_holes | 400 | 0.12 | 1 | 0.004 | 0.004 | 0.008 | 0.021 | 0.004 |
| grid_holes | 800 | 0.12 | 1 | 0.007 | 0.012 | 0.017 | 0.027 | 0.025 |
| two_spheres_apart | 300 | 1.4 | 2 | 0.018 | 0.087 | 0.098 | 0.054 | 0.782 |
| nonuniform_circle | 400 | 1.5 | 1 | 0.012 | 0.032 | 0.042 | 0.055 | 0.622 |
| mixed_1d2d3d | 300 | 1.4 | 2 |  |  |  |  |  |

## Construct vs reduce (1-thread exact, from `baselines.json`)
`metric_ms` is G_T / Delaunay construction; `collapse_ms` is flag collapse; `reduce_ms` is the pairing. Counters already stored; not a new bench.
| family | n | wall (s) | construct (s) | collapse (s) | reduce (s) | |E| in | residual |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| circle_noisy | 200 | 0.005 | 0.000 | 0.001 | 0.000 | 10880 | 0.026011029 |
| circle_noisy | 500 | 0.017 | 0.000 | 0.009 | 0.000 | 67370 | 0.023418364 |
| circle_noisy | 1000 | 0.068 | 0.002 | 0.046 | 0.001 | 270262 | 0.021094029 |
| figure8 | 500 | 0.010 | 0.000 | 0.004 | 0.000 | 31499 | 0.038026199 |
| figure8 | 1000 | 0.023 | 0.002 | 0.000 | 0.009 |  | 0.038005987 |
| figure8 | 2000 | 0.152 | 0.009 | 0.000 | 0.100 |  | 0.037981408 |
| sphere | 200 | 0.007 | 0.000 | 0.002 | 0.001 | 9708 | 0.073753605 |
| sphere | 400 | 0.017 | 0.000 | 0.008 | 0.001 | 39381 | 0.058835066 |
| uniform2 | 500 | 0.008 | 0.000 | 0.000 | 0.003 |  | 0.077009053 |
| uniform2 | 1000 | 0.018 | 0.002 | 0.000 | 0.009 |  | 0.081610446 |
| nested_loops | 400 | 0.009 | 0.000 | 0.000 | 0.004 |  | 0.089686668 |
| nested_loops | 1000 | 0.037 | 0.002 | 0.000 | 0.029 |  | 0.089188848 |
| many_loops | 400 | 0.004 | 0.000 | 0.000 | 0.001 |  | 0.095895666 |
| torus | 400 | 0.009 | 0.000 | 0.000 | 0.002 |  | 0.28690845 |
| torus | 1000 | 0.040 | 0.002 | 0.000 | 0.024 |  | 0.26158851 |
| disconnected_circles | 400 | 0.008 | 0.000 | 0.003 | 0.000 | 21469 | 0.033730876 |
| disconnected_circles | 1000 | 0.037 | 0.002 | 0.024 | 0.000 | 134903 | 0.034462199 |
| random_geometric_sparse | 500 | 0.006 | 0.000 | 0.000 | 0.002 |  | 0.29865424 |
| random_geometric_sparse | 1000 | 0.009 | 0.000 | 0.000 | 0.002 |  | 0.29103304 |
| random_geometric_dense | 400 | 0.009 | 0.000 | 0.000 | 0.002 |  | 0.044843049 |
| random_geometric_dense | 800 | 0.018 | 0.001 | 0.000 | 0.009 |  | 0.049310461 |
| grid_holes | 400 | 0.004 | 0.000 | 0.000 | 0.001 |  | 0.48821866 |
| grid_holes | 800 | 0.007 | 0.000 | 0.000 | 0.003 |  | 0.39789658 |
| two_spheres_apart | 300 | 0.018 | 0.000 | 0.000 | 0.014 |  | 0.12794255 |
| nonuniform_circle | 400 | 0.012 | 0.000 | 0.005 | 0.000 | 37773 | 0.026211439 |

## Phase-3 topology (exact engines vs Ripser; scale unmatched)
| family | n | PITH match | giotto match | GUDHI match | scale unmatched | scale bn H1 |
| --- | ---: | --- | --- | --- | ---: | ---: |
| circle_noisy | 400 | True | True | True | 0 | 4.6e-07 |
| figure8 | 400 | True | True | True | 0 | 5e-07 |
| disconnected_circles | 400 | True | True | True | 0 | 4.9e-07 |
| grid_holes | 400 | True | True | True | 0 | 4.1e-07 |
| nonuniform_circle | 400 | True | True | True | 0 | 4.7e-07 |
| two_spheres_apart | 300 | True | True | None | 45 | 0.0275 |

## Phase-3 held-out / post-freeze dispatcher
| family | n | recommended | auto | oracle | wrong | waste | regime |
| --- | ---: | --- | --- | --- | --- | ---: | --- |
| disconnected_circles | 400 | implicit | implicit | redzed | True | 1.28 | thin |
| disconnected_circles | 1000 | implicit | implicit | redzed | True | 1.37 | thin |
| random_geometric_sparse | 500 | redzed | redzed | redzed | False | 1.00 | hollow |
| random_geometric_dense | 400 | redzed | redzed | redzed | False | 1.00 | fat |
| grid_holes | 400 | redzed | redzed | redzed | False | 1.00 | hollow |
| grid_holes | 800 | redzed | redzed | redzed | False | 1.00 | hollow |
| two_spheres_apart | 300 | redzed | redzed | implicit | True | 2.75 | hollow |
| nonuniform_circle | 400 | implicit | implicit | redzed | True | 1.62 | thin |
| nested_loops | 1000 | redzed | redzed | redzed | False | 1.00 | fat |

## Phase-3 `--mode auto` vs probe
| family | n | selected | probe | match |
| --- | ---: | --- | --- | --- |
| disconnected_circles | 400 | exact | exact | True |
| disconnected_circles | 1000 | exact | exact | True |
| random_geometric_sparse | 500 | exact | exact | True |
| random_geometric_dense | 400 | exact | exact | True |
| grid_holes | 400 | exact | exact | True |
| grid_holes | 800 | exact | exact | True |
| two_spheres_apart | 300 | exact | exact | True |
| nonuniform_circle | 400 | exact | exact | True |
| nested_loops | 1000 | exact | exact | True |

## Phase-3 local exponents (new series)
| family | method | n0 | n1 | p_time |
| --- | --- | ---: | ---: | ---: |
| circle_noisy | pith_exact_t1 | 200 | 500 | 1.32 |
| circle_noisy | pith_exact_t1 | 500 | 1000 | 1.98 |
| circle_noisy | pith_redzed_t1 | 200 | 500 | 1.83 |
| circle_noisy | pith_redzed_t1 | 500 | 1000 | 2.29 |
| circle_noisy | ripser | 200 | 500 | 3.23 |
| circle_noisy | ripser | 500 | 1000 | 2.85 |
| circle_noisy | giotto_t1 | 200 | 500 | 3.02 |
| circle_noisy | giotto_t1 | 500 | 1000 | 2.82 |
| circle_noisy | giotto_t4 | 200 | 500 | 2.51 |
| circle_noisy | giotto_t4 | 500 | 1000 | 2.77 |
| circle_noisy | gudhi_rips | 200 | 500 | 3.28 |
| circle_noisy | pith_scale_t1 | 200 | 500 | 1.03 |
| circle_noisy | pith_scale_t1 | 500 | 1000 | 1.11 |
| figure8 | pith_exact_t1 | 500 | 1000 | 1.19 |
| figure8 | pith_exact_t1 | 1000 | 2000 | 2.74 |
| figure8 | pith_redzed_t1 | 500 | 1000 | 1.69 |
| figure8 | pith_redzed_t1 | 1000 | 2000 | 2.72 |
| figure8 | ripser | 500 | 1000 | 2.34 |
| figure8 | ripser | 1000 | 2000 | 4.00 |
| figure8 | giotto_t1 | 500 | 1000 | 2.24 |
| figure8 | giotto_t1 | 1000 | 2000 | 3.87 |
| figure8 | giotto_t4 | 500 | 1000 | 1.50 |
| figure8 | giotto_t4 | 1000 | 2000 | 4.23 |
| figure8 | gudhi_rips | 500 | 1000 | 3.24 |
| sphere | pith_exact_t1 | 200 | 400 | 1.25 |
| sphere | pith_redzed_t1 | 200 | 400 | 3.40 |
| sphere | ripser | 200 | 400 | 3.03 |
| sphere | giotto_t1 | 200 | 400 | 2.98 |
| sphere | giotto_t4 | 200 | 400 | 2.78 |
| sphere | pith_scale_t1 | 200 | 400 | 1.03 |
| uniform2 | pith_exact_t1 | 500 | 1000 | 1.16 |
| uniform2 | pith_redzed_t1 | 500 | 1000 | 1.48 |
| uniform2 | ripser | 500 | 1000 | 1.87 |
| uniform2 | giotto_t1 | 500 | 1000 | 1.76 |
| uniform2 | giotto_t4 | 500 | 1000 | 1.29 |
| uniform2 | gudhi_rips | 500 | 1000 | 3.25 |
| nested_loops | pith_exact_t1 | 400 | 1000 | 1.56 |
| nested_loops | pith_redzed_t1 | 400 | 1000 | 1.81 |
| nested_loops | ripser | 400 | 1000 | 2.69 |
| nested_loops | giotto_t1 | 400 | 1000 | 2.65 |
| nested_loops | giotto_t4 | 400 | 1000 | 2.39 |
| nested_loops | gudhi_rips | 400 | 1000 | 3.30 |
| torus | pith_exact_t1 | 400 | 1000 | 1.65 |
| torus | pith_redzed_t1 | 400 | 1000 | 1.97 |
| torus | ripser | 400 | 1000 | 2.96 |
| torus | giotto_t1 | 400 | 1000 | 2.85 |
| torus | giotto_t4 | 400 | 1000 | 2.48 |
| torus | gudhi_rips | 400 | 1000 | 3.31 |
| disconnected_circles | pith_exact_t1 | 400 | 1000 | 1.70 |
| disconnected_circles | pith_redzed_t1 | 400 | 1000 | 1.81 |
| disconnected_circles | ripser | 400 | 1000 | 2.96 |
| disconnected_circles | giotto_t1 | 400 | 1000 | 2.87 |
| disconnected_circles | giotto_t4 | 400 | 1000 | 2.54 |
| disconnected_circles | gudhi_rips | 400 | 1000 | 3.40 |
| disconnected_circles | pith_scale_t1 | 400 | 1000 | 1.10 |
| random_geometric_sparse | pith_exact_t1 | 500 | 1000 | 0.66 |
| random_geometric_sparse | pith_redzed_t1 | 500 | 1000 | 0.69 |
| random_geometric_sparse | ripser | 500 | 1000 | 1.68 |
| random_geometric_sparse | giotto_t1 | 500 | 1000 | 1.35 |
| random_geometric_sparse | giotto_t4 | 500 | 1000 | 0.67 |
| random_geometric_sparse | gudhi_rips | 500 | 1000 | 3.06 |
| random_geometric_dense | pith_exact_t1 | 400 | 800 | 1.06 |
| random_geometric_dense | pith_redzed_t1 | 400 | 800 | 1.55 |
| random_geometric_dense | ripser | 400 | 800 | 2.12 |
| random_geometric_dense | giotto_t1 | 400 | 800 | 2.00 |
| random_geometric_dense | giotto_t4 | 400 | 800 | 1.44 |
| random_geometric_dense | gudhi_rips | 400 | 800 | 3.32 |
| grid_holes | pith_exact_t1 | 400 | 800 | 0.86 |
| grid_holes | pith_redzed_t1 | 400 | 800 | 1.06 |
| grid_holes | ripser | 400 | 800 | 1.62 |
| grid_holes | giotto_t1 | 400 | 800 | 1.12 |
| grid_holes | giotto_t4 | 400 | 800 | 0.39 |
| grid_holes | gudhi_rips | 400 | 800 | 2.84 |
| grid_holes | pith_scale_t1 | 400 | 800 | 1.11 |

## Sparse Rips (ε=0.6 greedy net) vs VR / scale
Not exact VR. Sheehy-style interleaving is the literature guarantee; numbers are measured.
`distances` is pairwise construction; report `edges_in` as |E| (do not use distances).
| family | n | exact (s) | scale (s) | sparse (s) | sparse |E| | unmatched | bn H1 | W1 H1 | sparse ess |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| figure8 | 400 | 0.007 | 0.005 | 0.004 | 5563 | 14 | 0.007142 | 0.02282 | H1=2 H2=None |
| circle_noisy | 400 | 0.014 | 0.005 | 0.006 | 7689 | 30 | 0.006245 | 0.03413 | H1=1 H2=None |
| nested_loops | 400 | 0.009 | 0.007 | 0.006 | 5061 | 52 | 0.1109 | 1.047 | H1=1 H2=None |
| many_loops | 400 | 0.004 | 0.005 | 0.003 | 3318 | 8 | 0.02809 | 0.04283 | H1=5 H2=None |
| disconnected_circles | 400 | 0.008 | 0.006 | 0.004 | 5605 | 18 | 0.01729 | 0.05858 | H1=2 H2=None |
| grid_holes | 400 | 0.004 | 0.004 | 0.003 | 2672 | 0 | 4.1e-07 | 7.507e-06 | H1=2 H2=None |
| sphere | 400 | 0.017 | 0.006 |  | None | None |  |  | H1=None H2=None |
| two_spheres_apart | 300 | 0.019 | 0.005 | 3.708 | 5730 | 41 | 0.03888 | 0.314 | H1=0 H2=2 |

## Failure pushes (12 s)
| family | n | PITH exact | Ripser | giotto t1 |
| --- | ---: | --- | --- | --- |
| circle_noisy | 2000 | 0.338 | timeout | timeout |
| figure8 | 4000 | 1.022 |  | timeout |
| sphere | 800 | 0.058 |  | timeout |
| nested_loops | 2000 | 0.303 |  | 7.225 |

## Fused sparse scaling (1 thread, no n×n matrix)
Same greedy-net flag as the matrix path. `distances` is FPS + T-ball evals. Local p is empirical, not a theorem.
| family | n | sparse (s) | scale (s) | construct (s) | reduce (s) | sparse |E| | sparse RSS | local p | ess H1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| figure8 | 2000 | 0.049 | 0.035 | 0.022 | 0.024 | 57625 | 8 MB |  | 2 |
| figure8 | 4000 | 0.163 | 0.084 | 0.083 | 0.074 | 150916 | 14 MB | 1.73 | 2 |
| figure8 | 8000 | 0.645 | 0.219 | 0.369 | 0.263 | 382584 | 30 MB | 1.98 | 2 |
| figure8 | 12000 | 1.456 | 0.361 | 0.952 | 0.489 | 645603 | 47 MB | 2.01 | 2 |
| figure8 | 16000 | 2.588 | 0.498 | 1.781 | 0.787 | 928616 | 66 MB | 2.00 | 2 |
| figure8 | 24000 | 5.558 | 0.816 | 4.245 | 1.284 | 1559003 | 106 MB | 1.89 | 2 |
| circle_noisy | 2000 | 0.072 | 0.036 | 0.029 | 0.040 | 76625 | 10 MB |  | 1 |
| circle_noisy | 4000 | 0.250 | 0.092 | 0.108 | 0.136 | 192862 | 17 MB | 1.79 | 1 |
| circle_noisy | 8000 | 0.977 | 0.231 | 0.482 | 0.484 | 477475 | 38 MB | 1.96 | 1 |
| circle_noisy | 12000 | 1.928 | 0.361 | 1.155 | 0.758 | 792854 | 60 MB | 1.68 | 1 |
| nested_loops | 2000 | 0.059 | 0.038 | 0.021 | 0.035 | 47964 | 8 MB |  | 1 |
| nested_loops | 4000 | 0.168 | 0.076 | 0.079 | 0.084 | 127154 | 14 MB | 1.51 | 1 |
| nested_loops | 8000 | 0.758 | 0.203 | 0.348 | 0.400 | 325874 | 39 MB | 2.17 | 1 |
| disconnected_circles | 2000 | 0.053 | 0.035 | 0.020 | 0.030 | 58960 | 8 MB |  | 2 |
| disconnected_circles | 4000 | 0.167 | 0.085 | 0.075 | 0.085 | 151599 | 14 MB | 1.66 | 2 |
| disconnected_circles | 8000 | 0.635 | 0.225 | 0.348 | 0.274 | 382936 | 29 MB | 1.93 | 2 |
| uniform4 | 400 | 0.026 |  | 0.003 | 0.022 | 32217 | 7 MB |  | 0 |
| uniform4 | 800 | 0.072 |  | 0.010 | 0.059 | 93659 | 13 MB | 1.44 | 0 |
| uniform4 | 1600 | 0.268 |  | 0.034 | 0.229 | 266831 | 38 MB | 1.91 | 0 |

## `--mode auto` vs probe (`eval_mode_auto.py`)
Agreement 10/10. `refuse` means the probe named sparse but auto exits 3 instead of starting fat H2 outside d∈{2,3}.
| family | n | maxdim | selected | expect | refused | agree |
| --- | ---: | ---: | --- | --- | --- | --- |
| circle_noisy | 400 | 1 | exact | exact | False | True |
| figure8 | 400 | 1 | exact | exact | False | True |
| many_loops | 400 | 1 | exact | exact | False | True |
| nested_loops | 400 | 1 | exact | exact | False | True |
| sphere | 400 | 2 | exact | exact | False | True |
| mixed_1d2d3d | 300 | 2 | scale | scale | False | True |
| figure8 | 16000 | 1 | scale | scale | False | True |
| sphere | 16000 | 2 | scale | scale | False | True |
| uniform4 | 5000 | 1 | sparse | sparse | False | True |
| uniform4 | 250 | 2 | sparse | refuse | True | True |

## `--estimate` vs measured wall (`eval_estimate.py`)
Recommended-mode wall inside `[est_runtime_lo, est_runtime_hi]`: 32/32. Empirical bands; τ frozen.
| family | n | maxdim | rec | wall (s) | lo | hi | ratio | in band |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- |
| circle_noisy | 200 | 1 | exact | 0.005 | 0.003 | 0.026 | 0.78 | True |
| circle_noisy | 400 | 1 | exact | 0.014 | 0.005 | 0.046 | 1.26 | True |
| circle_noisy | 500 | 1 | exact | 0.017 | 0.006 | 0.060 | 1.15 | True |
| circle_noisy | 1000 | 1 | exact | 0.068 | 0.018 | 0.180 | 1.52 | True |
| circle_noisy | 2000 | 1 | exact |  | 0.066 | 0.660 |  | None |
| circle_noisy | 4000 | 1 | exact |  | 0.258 | 2.580 |  | None |
| circle_noisy | 8000 | 1 | scale | 0.231 | 0.112 | 1.120 | 0.83 | True |
| circle_noisy | 12000 | 1 | scale | 0.361 | 0.168 | 1.680 | 0.86 | True |
| disconnected_circles | 400 | 1 | exact | 0.008 | 0.005 | 0.046 | 0.67 | True |
| disconnected_circles | 1000 | 1 | exact | 0.037 | 0.018 | 0.180 | 0.82 | True |
| disconnected_circles | 2000 | 1 | exact |  | 0.066 | 0.660 |  | None |
| disconnected_circles | 4000 | 1 | exact |  | 0.258 | 2.580 |  | None |
| disconnected_circles | 8000 | 1 | scale | 0.225 | 0.112 | 1.120 | 0.80 | True |
| figure8 | 400 | 1 | exact | 0.007 | 0.003 | 0.028 | 1.03 | True |
| figure8 | 500 | 1 | exact | 0.010 | 0.006 | 0.060 | 0.67 | True |
| figure8 | 1000 | 1 | exact | 0.023 | 0.007 | 0.069 | 1.32 | True |
| figure8 | 2000 | 1 | exact | 0.152 | 0.021 | 0.213 | 2.85 | True |
| figure8 | 4000 | 1 | exact |  | 0.080 | 0.801 |  | None |
| figure8 | 8000 | 1 | scale | 0.219 | 0.112 | 1.120 | 0.78 | True |
| figure8 | 12000 | 1 | scale | 0.361 | 0.168 | 1.680 | 0.86 | True |
| figure8 | 16000 | 1 | scale | 0.498 | 0.224 | 2.240 | 0.89 | True |
| figure8 | 24000 | 1 | scale | 0.816 | 0.336 | 3.360 | 0.97 | True |
| grid_holes | 400 | 1 | exact | 0.004 | 0.002 | 0.025 | 0.70 | True |
| grid_holes | 800 | 1 | exact | 0.007 | 0.002 | 0.025 | 1.13 | True |
| many_loops | 400 | 1 | exact | 0.004 | 0.002 | 0.025 | 0.65 | True |
| mixed_1d2d3d | 300 | 2 | scale | 0.005 | 0.002 | 0.036 | 0.86 | True |
| nested_loops | 400 | 1 | exact | 0.009 | 0.003 | 0.028 | 1.29 | True |
| nested_loops | 1000 | 1 | exact | 0.037 | 0.007 | 0.071 | 2.10 | True |
| nested_loops | 2000 | 1 | exact |  | 0.023 | 0.227 |  | None |
| nested_loops | 4000 | 1 | exact |  | 0.083 | 0.831 |  | None |
| nested_loops | 8000 | 1 | scale | 0.203 | 0.112 | 1.120 | 0.73 | True |
| nonuniform_circle | 400 | 1 | exact | 0.012 | 0.005 | 0.046 | 1.02 | True |
| sphere | 200 | 2 | exact | 0.007 | 0.003 | 0.026 | 1.10 | True |
| sphere | 400 | 2 | exact | 0.017 | 0.005 | 0.046 | 1.53 | True |
| torus | 400 | 1 | exact | 0.009 | 0.003 | 0.028 | 1.29 | True |
| torus | 1000 | 1 | exact | 0.040 | 0.007 | 0.067 | 2.39 | True |
| two_spheres_apart | 300 | 2 | exact | 0.019 | 0.002 | 0.025 | 3.11 | True |
| uniform2 | 500 | 1 | exact | 0.008 | 0.003 | 0.034 | 0.91 | True |
| uniform2 | 1000 | 1 | exact | 0.018 | 0.007 | 0.073 | 0.96 | True |
| uniform4 | 400 | 1 | exact |  | 0.005 | 0.046 |  | None |
| uniform4 | 800 | 1 | exact |  | 0.012 | 0.121 |  | None |
| uniform4 | 1600 | 1 | exact |  | 0.043 | 0.429 |  | None |

## Engine oracle live check (`eval_engine_auto.py`)
Oracle 5/9. New misses: none. Known misses waived; τ frozen.
| family | n | rec | oracle | wrong | waived | waste |
| --- | ---: | --- | --- | --- | --- | ---: |
| disconnected_circles | 400 | implicit | redzed | True | True | 1.18 |
| disconnected_circles | 1000 | implicit | redzed | True | True | 1.34 |
| random_geometric_sparse | 500 | redzed | redzed | False | False | 1.00 |
| random_geometric_dense | 400 | redzed | redzed | False | False | 1.00 |
| grid_holes | 400 | redzed | redzed | False | False | 1.00 |
| grid_holes | 800 | redzed | redzed | False | False | 1.00 |
| two_spheres_apart | 300 | redzed | implicit | True | True | 2.71 |
| nonuniform_circle | 400 | implicit | redzed | True | True | 1.59 |
| nested_loops | 1000 | redzed | redzed | False | False | 1.00 |

## `wall_kind` vs measured share (`eval_wall_kind.py`)
Agreement 20/20. Measured kind is the largest of metric/collapse/reduce (n≥400, ≥1 ms).
| family | n | measured | estimate | regime | agree |
| --- | ---: | --- | --- | --- | --- |
| circle_noisy | 500 | collapse | collapse | thin | True |
| circle_noisy | 1000 | collapse | collapse | thin | True |
| figure8 | 500 | collapse | collapse | thin | True |
| figure8 | 1000 | leftover | leftover | hollow | True |
| figure8 | 2000 | leftover | leftover | hollow | True |
| sphere | 400 | collapse | collapse | thin | True |
| uniform2 | 500 | leftover | leftover | fat | True |
| uniform2 | 1000 | leftover | leftover | fat | True |
| nested_loops | 400 | leftover | leftover | fat | True |
| nested_loops | 1000 | leftover | leftover | fat | True |
| torus | 400 | leftover | leftover | hollow | True |
| torus | 1000 | leftover | leftover | hollow | True |
| disconnected_circles | 400 | collapse | collapse | thin | True |
| disconnected_circles | 1000 | collapse | collapse | thin | True |
| random_geometric_sparse | 500 | leftover | leftover | hollow | True |
| random_geometric_sparse | 1000 | leftover | leftover | hollow | True |
| random_geometric_dense | 400 | leftover | leftover | fat | True |
| random_geometric_dense | 800 | leftover | leftover | fat | True |
| grid_holes | 800 | leftover | leftover | hollow | True |
| nonuniform_circle | 400 | collapse | collapse | thin | True |

## Leftover-family exact H1 vs Ripser (`reverify_leftover_10x.py`)
1-thread. 3/6 ≥10×. Same pairing class; constant-factor only.
| family | n | PITH (s) | Ripser (s) | ratio | reduce (ms) | pipeline |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| figure8 | 2000 | 0.147 | 2.499 | 17.03× | 95 | pith:auto-redzed-spatial |
| torus | 2000 | 0.206 | 2.607 | 12.64× | 150 | pith:auto-redzed-spatial |
| uniform2 | 2000 | 0.077 | 0.444 | 5.76× | 46 | pith:auto-redzed |
| uniform2 | 5000 | 0.398 | 3.246 | 8.15× | 287 | pith:auto-redzed |
| sphere | 2000 | 0.092 | 0.784 | 8.48× | 61 | pith:auto-redzed |
| blobs | 4000 | 0.165 | 2.131 | 12.94× | 145 | pith:auto-redzed-cc |
