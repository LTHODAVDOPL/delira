from typing import Optional, Union, Iterable, ClassVar, Callable
from functools import partial

from delira.models.backends.chainer import AbstractChainerNetwork
from delira.data_loading import BaseDataManager
from delira.training.base_experiment import BaseExperiment
from delira.training.base_trainer import BaseNetworkTrainer
from delira.training.parameters import Parameters

from delira.training.backends.chainer.utils import create_optims_default
from delira.training.backends.chainer.utils import convert_to_numpy
from delira.training.backends.chainer.trainer import ChainerNetworkTrainer


class ChainerExperiment(BaseExperiment):
    def __init__(
            self,
            params: Union[str, Parameters],
            model_cls: AbstractChainerNetwork,
            n_epochs: Optional[int] = None,
            name: Optional[str] = None,
            save_path: Optional[str] = None,
            key_mapping: Optional[dict] = None,
            val_score_key: Optional[str] = None,
            optim_builder: Callable = create_optims_default,
            checkpoint_freq: int = 1,
            trainer_cls: ClassVar[BaseNetworkTrainer] = ChainerNetworkTrainer,
            **kwargs):
        """

        Parameters
        ----------
        params : :class:`Parameters` or str
            the training parameters, if string is passed,
            it is treated as a path to a pickle file, where the
            parameters are loaded from
        model_cls : Subclass of :class:`AbstractChainerNetwork`
            the class implementing the model to train
        n_epochs : int or None
            the number of epochs to train, if None: can be specified later
            during actual training
        name : str or None
            the Experiment's name
        save_path : str or None
            the path to save the results and checkpoints to.
            if None: Current working directory will be used
        key_mapping : dict
            mapping between data_dict and model inputs (necessary for
            prediction with :class:`Predictor`-API), if no keymapping is
            given, a default key_mapping of {"x": "data"} will be used here
        val_score_key : str or None
            key defining which metric to use for validation (determining
            best model and scheduling lr); if None: No validation-based
            operations will be done (model might still get validated,
            but validation metrics can only be logged and not used further)
        optim_builder : function
            Function returning a dict of backend-specific optimizers.
            defaults to :func:`create_optims_default_chainer`
        checkpoint_freq : int
            frequency of saving checkpoints (1 denotes saving every epoch,
            2 denotes saving every second epoch etc.); default: 1
        trainer_cls : subclass of :class:`ChainerNetworkTrainer`
            the trainer class to use for training the model, defaults to
            :class:`ChainerNetworkTrainer`
        **kwargs :
            additional keyword arguments

        """

        if key_mapping is None:
            key_mapping = {"x": "data"}
        super().__init__(params=params, model_cls=model_cls,
                         n_epochs=n_epochs, name=name, save_path=save_path,
                         key_mapping=key_mapping,
                         val_score_key=val_score_key,
                         optim_builder=optim_builder,
                         checkpoint_freq=checkpoint_freq,
                         trainer_cls=trainer_cls,
                         **kwargs)

    def test(self, network: AbstractChainerNetwork,
             test_data: BaseDataManager,
             metrics: dict, metric_keys: Optional[dict] = None,
             verbose: bool = False, prepare_batch: Optional[Callable] = None,
             convert_fn: Callable = convert_to_numpy, **kwargs):
        """
        Setup and run testing on a given network

        Parameters
        ----------
        network : :class:`AbstractNetwork`
            the (trained) network to test
        test_data : :class:`BaseDataManager`
            the data to use for testing
        metrics : dict
            the metrics to calculate
        metric_keys : dict of tuples
            the batch_dict keys to use for each metric to calculate.
            Should contain a value for each key in ``metrics``.
            If no values are given for a key, per default ``pred`` and
            ``label``
             will be used for metric calculation
        verbose : bool
            verbosity of the test process
        prepare_batch : function
            function to convert a batch-dict to a format accepted by the
            model. This conversion typically includes dtype-conversion,
            reshaping, wrapping to backend-specific tensors and
            pushing to correct devices. If not further specified uses the
            ``network``'s ``prepare_batch`` with CPU devices
        convert_fn : function
            function to convert a batch of tensors to numpy
            if not specified defaults to
            :func:`convert_chainer_tensor_to_npy`

        **kwargs :
            additional keyword arguments

        Returns
        -------
        dict
            all predictions obtained by feeding the ``test_data`` through
            the ``network``
        dict
            all metrics calculated upon the ``test_data`` and the obtained
            predictions

        """

        # use backend-specific and model-specific prepare_batch fn
        # (runs on same device as passed network per default)

        device = network.device
        if prepare_batch is None:
            prepare_batch = partial(network.prepare_batch,
                                    input_device=device,
                                    output_device=device)

        return super().test(network=network, test_data=test_data,
                            metrics=metrics, metric_keys=metric_keys,
                            verbose=verbose, prepare_batch=prepare_batch,
                            convert_fn=convert_fn, **kwargs)
