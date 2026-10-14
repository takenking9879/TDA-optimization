#pragma once

#include <algorithm>
#include <thread>

namespace pith {

// 0 means "use hardware_concurrency". Set from --threads before any
// parallel scan so 1-thread comparisons are honest.
inline int& thread_limit_storage() {
    static int limit = 0;
    return limit;
}

inline void set_thread_limit(int n) { thread_limit_storage() = n; }

inline int hardware_threads() {
    const unsigned hw = std::thread::hardware_concurrency();
    return std::max(1, static_cast<int>(hw ? hw : 1));
}

inline int nthreads() {
    const int hw = hardware_threads();
    const int lim = thread_limit_storage();
    if (lim <= 0) return hw;
    return std::max(1, std::min(lim, hw));
}

}  // namespace pith
