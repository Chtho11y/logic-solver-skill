# meta — compile-time uniqueness helpers (META_SOLVE_PLAN.md)
# Call from a top-level (unguarded) site. ``meta:`` inside this def is allowed;
# the caller's guards must be empty.

def assert_unique(v):
    meta:
        unique_over(v)
        let s1 = solve()
        require(s1.sat, "UNSAT: encoding rejects the intended answer")
        scope:
            exclude(s1)
            let s2 = solve()
        require(not s2.sat, "MULTIPLE: encoding admits more than one solution")
