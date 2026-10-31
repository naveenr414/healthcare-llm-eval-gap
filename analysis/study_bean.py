"""Public entry points for every Bean et al. analysis."""

from _bean_information import main as information_decomposition
from _bean_model_comparison import main as model_comparison
from _bean_report import main as report


def run(run_api=False, prepare_e2=False, limit=None, workers=8,
        n_boot=5000, validate=True):
    """Run Bean's report, information decomposition, and model comparison."""
    report()
    information_decomposition(
        run_api=run_api,
        prepare_e2=prepare_e2,
        limit=limit,
        workers=workers,
    )
    model_comparison(n_boot=n_boot, validate=validate)


if __name__ == '__main__':
    run()
