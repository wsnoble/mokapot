"""
This is the command line interface for mokapot
"""
import os
import sys
import logging

import numpy as np

from mokapot import __version__
from .config import Config
from .parsers import read_pin
from .brew import brew
from .model import PercolatorModel, DaskModel

try:
    from dask.distributed import Client
    DASK_AVAIL = True
except ImportError:
    DASK_AVAIL = False

def main():
    """The CLI entry point"""
    # Get command line arguments
    config = Config()

    # Setup logging
    verbosity_dict = {0: logging.ERROR,
                      1: logging.WARNING,
                      2: logging.INFO,
                      3: logging.DEBUG}

    logging.basicConfig(format=("[{levelname}] {message}"),
                        style="{", level=verbosity_dict[config.verbosity])

    logging.info("mokapot version %s", str(__version__))
    logging.info("Written by William E. Fondrie (wfondrie@uw.edu) in the")
    logging.info("Department of Genome Sciences at the University of "
                 "Washington.")
    logging.info("Command issued:")
    logging.info("%s", " ".join(sys.argv))
    logging.info("")
    logging.info("Starting Analysis")
    logging.info("=================")

    np.random.seed(config.seed)

    # Make model
    if config.use_dask:
        if DASK_AVAIL:
            client = Client()
            model = DaskModel()
        else:
            raise ImportError("dask and dask-ml must be installed to use the"
                              "'--use_dask' flag.")
    else:
        model = PercolatorModel()

    # Parse PSMs
    if config.aggregate or len(config.pin_files) == 1:
        datasets = read_pin(config.pin_files, use_dask=config.use_dask)
    else:
        datasets = [read_pin(f, use_dask=config.use_dask)
                    for f in config.pin_files]
        prefixes = [os.path.splitext(os.path.basename(f))[0]
                    for f in config.pin_files]

    psms = brew(datasets,
                model,
                train_fdr=config.train_fdr,
                test_fdr=config.test_fdr,
                max_iter=config.max_iter,
                direction=config.direction,
                folds=config.folds)

    if config.aggregate or len(config.pin_files) == 1:
        psms.to_txt(dest_dir=config.dest_dir, file_root=config.file_root)
    else:
        for dat, prefix in zip(psms, prefixes):
            if config.file_root is not None:
                prefix = ".".join([config.file_root, prefix])

            dat.to_txt(dest_dir=config.dest_dir, file_root=prefix)


if __name__ == "__main__":
    main()
