from tests.test_h1 import test_noise_filter
from tests.test_h2 import test_localization_requires_four_sensors
from tests.test_h3 import test_context_builder
from tests.test_grade_engine import test_grade_is_iv_when_localization_fails
from tests.test_engine import test_complete_pipeline

print("Running tests...")

test_noise_filter()
print("✓ H1")

test_localization_requires_four_sensors()
print("✓ H2")

test_grade_is_iv_when_localization_fails()
print("✓ Grade Engine")

test_context_builder()
print("✓ H3")

test_complete_pipeline()
print("✓ Engine")

print("\nAll tests passed!")