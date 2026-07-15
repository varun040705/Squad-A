from tests.test_h1 import test_noise_filter, test_zero_duration_treated_as_noise
from tests.test_h2 import (
    test_localization_requires_four_sensors,
    test_localization_without_sensor_positions_flags_not_estimates,
    test_localization_triangulates_with_known_geometry,
    test_localization_flags_degenerate_coplanar_geometry,
    test_load_history_requires_load_samples,
    test_load_history_computes_calm_and_felicity_ratio,
)
from tests.test_h3 import (
    test_context_builder_grade_undetermined_when_no_load_history,
    test_context_builder_grades_when_felicity_available,
)
from tests.test_engine import test_complete_pipeline

print("Running tests...")

test_noise_filter()
test_zero_duration_treated_as_noise()
print("check H1")

test_localization_requires_four_sensors()
test_localization_without_sensor_positions_flags_not_estimates()
test_localization_triangulates_with_known_geometry()
test_localization_flags_degenerate_coplanar_geometry()
test_load_history_requires_load_samples()
test_load_history_computes_calm_and_felicity_ratio()
print("check H2")

test_context_builder_grade_undetermined_when_no_load_history()
test_context_builder_grades_when_felicity_available()
print("check H3")

test_complete_pipeline()
print("check Engine")

print("All tests passed!")