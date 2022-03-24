# pytype: skip-file
from typing import NamedTuple
import torch
from norse.torch.functional.lif import (
    LIFFeedForwardState,
    lif_feed_forward_step,
    lif_step,
    LIFState,
    LIFParameters,
)

from norse.torch.functional.lif_refrac import LIFRefracState
from norse.torch.module import lif, snn, lif_refrac



class MockParams(NamedTuple):
    my_param: int = -15
    method: str = "bob"


def test_snn_recurrent_cell_weights():
    in_w = torch.randn(3, 2)
    re_w = torch.randn(3, 3)
    n = snn.SNNRecurrentCell(
        None, None, 2, 3, p=MockParams(), input_weights=in_w, recurrent_weights=re_w
    )
    assert torch.all(torch.eq(n.input_weights, in_w))
    assert torch.all(torch.eq(n.recurrent_weights, re_w))


def test_snn_recurrent_cell_weights_no_autapses():
    in_w = torch.randn(3, 2)
    re_w = torch.randn(3, 3) * (torch.eye(3) - 1) * -1

    n = snn.SNNRecurrentCell(
        None,
        None,
        2,
        3,
        p=MockParams(),
        input_weights=in_w,
        recurrent_weights=re_w,
        autapses=False,
    )
    assert torch.all(torch.eq(n.input_weights, in_w))
    assert torch.all(torch.eq(n.recurrent_weights, re_w))


def test_snn_recurrent_cell_weights_autapse_update():
    in_w = torch.ones(3, 2)
    re_w = torch.nn.Parameter(torch.ones(3, 3))
    n = snn.SNNRecurrentCell(
        lif_step,
        lambda x: LIFState(v=torch.zeros(3), i=torch.zeros(3), z=torch.ones(3)),
        2,
        3,
        p=LIFParameters(v_th=torch.as_tensor(0.1)),
        input_weights=in_w,
        recurrent_weights=re_w,
    )
    assert torch.all(torch.eq(n.recurrent_weights.diag(), torch.zeros(3)))
    optim = torch.optim.Adam(n.parameters())
    optim.zero_grad()
    spikes = []
    s = None
    for _ in range(10):
        z, s = n(torch.ones(2), s)
        spikes.append(z)
    spikes = torch.stack(spikes)
    loss = spikes.sum()
    loss.backward()
    optim.step()
    w = n.recurrent_weights.clone().detach()
    assert not z.sum() == 0.0
    assert torch.all(torch.eq(w.diag(), torch.zeros(3)))
    w.fill_diagonal_(1.0)
    assert not torch.all(torch.eq(w, torch.ones(3, 3)))


def test_snn_recurrent_weights():
    in_w = torch.randn(3, 2)
    re_w = torch.randn(3, 3)
    n = snn.SNNRecurrent(
        None, None, 2, 3, p=MockParams(), input_weights=in_w, recurrent_weights=re_w
    )
    assert torch.all(torch.eq(n.input_weights, in_w))
    assert torch.all(torch.eq(n.recurrent_weights, re_w))


def test_snn_recurrent_weights_no_autapses():
    in_w = torch.randn(3, 2)
    re_w = torch.randn(3, 3) * (torch.eye(3) - 1) * -1
    n = snn.SNNRecurrent(
        None,
        None,
        2,
        3,
        p=MockParams(),
        input_weights=in_w,
        recurrent_weights=re_w,
        autapses=False,
    )
    assert torch.all(torch.eq(n.input_weights, in_w))
    assert torch.all(torch.eq(n.recurrent_weights, re_w))


def test_snn_recurrent_weights_autapse_update():
    in_w = torch.ones(3, 2)
    re_w = torch.nn.Parameter(torch.ones(3, 3))
    n = snn.SNNRecurrent(
        lif_step,
        lambda x: LIFState(v=torch.zeros(3), i=torch.zeros(3), z=torch.ones(3)),
        2,
        3,
        p=LIFParameters(v_th=torch.as_tensor(0.1)),
        input_weights=in_w,
        recurrent_weights=re_w,
    )
    assert torch.all(torch.eq(n.recurrent_weights.diag(), torch.zeros(3)))
    optim = torch.optim.Adam(n.parameters())
    optim.zero_grad()
    z, s = n(torch.ones(1, 2))
    z, _ = n(torch.ones(1, 2), s)
    loss = z.sum()
    loss.backward()
    optim.step()
    w = n.recurrent_weights.clone().detach()
    assert torch.all(torch.eq(w.diag(), torch.zeros(3)))


def test_snn_cell_repr():
    n = snn.SNNCell(None, None, p=MockParams())
    assert str(n) == f"SNNCell(p={MockParams()}, dt=0.001)"
    n = lif.LIFCell(p=LIFParameters())
    assert str(n) == f"LIFCell(p={LIFParameters()}, dt=0.001)"


def test_snn_recurrent_cell_repr():
    n = snn.SNNRecurrentCell(None, None, 1, 2, MockParams())
    assert (
        str(n)
        == f"SNNRecurrentCell(input_size=1, hidden_size=2, p={MockParams()}, autapses=False, dt=0.001)"
    )
    n = lif.LIFRecurrentCell(1, 2, p=LIFParameters())
    assert (
        str(n)
        == f"LIFRecurrentCell(input_size=1, hidden_size=2, p={LIFParameters()}, autapses=False, dt=0.001)"
    )


def test_snn_repr():
    n = snn.SNN(None, None, p=MockParams())
    assert str(n) == f"SNN(p={MockParams()}, dt=0.001)"
    n = lif.LIF(p=LIFParameters())
    assert str(n) == f"LIF(p={LIFParameters()}, dt=0.001)"


def test_snn_record_state():
    n = snn.SNN(
        lif_feed_forward_step,
        lambda x: LIFFeedForwardState(v=torch.zeros(1), i=torch.zeros(1)),
        p=LIFParameters(v_th=torch.as_tensor(0.1)),
        record_states=False,
    )
    _, y = n(torch.zeros(3, 1))
    assert isinstance(y, LIFFeedForwardState)

    n = snn.SNN(
        lif_feed_forward_step,
        lambda x: LIFFeedForwardState(v=torch.zeros(1), i=torch.zeros(1)),
        p=LIFParameters(v_th=torch.as_tensor(0.1)),
        record_states=True,
    )
    _, y = n(torch.zeros(3, 1))
    assert isinstance(y, LIFFeedForwardState)
    assert y.v.shape == (3, 1)
    assert y.i.shape == (3, 1)


def test_snn_recurrent_record_state():
    n = snn.SNNRecurrent(
        lif_step,
        lambda x: LIFState(v=torch.zeros(4), i=torch.zeros(4), z=torch.ones(4)),
        2,
        4,
        p=LIFParameters(v_th=torch.as_tensor(0.1)),
        record_states=False,
    )
    _, y = n(torch.zeros(3, 2))
    assert isinstance(y, LIFState)

    assert y.v.shape == (4,)
    assert y.i.shape == (4,)
    assert y.z.shape == (4,)

    n = snn.SNNRecurrent(
        lif_step,
        lambda x: LIFState(v=torch.zeros(4), i=torch.zeros(4), z=torch.ones(4)),
        2,
        4,
        p=LIFParameters(v_th=torch.as_tensor(0.1)),
        record_states=True,
    )
    _, y = n(torch.zeros(3, 2))

    assert isinstance(y, LIFState)
    assert y.v.shape == (3, 4)
    assert y.i.shape == (3, 4)
    assert y.z.shape == (3, 4)


def test_snn_record_nested_state():
    n = lif_refrac.LIFRefracRecurrent(
        2,
        4,
        record_states=True,
    )
    _, y = n(torch.zeros(3, 2))
    assert isinstance(y, LIFRefracState)
    assert isinstance(y.lif, LIFState)
    assert y.rho.shape == (3, 4)


def test_snn_recurrent_repr():
    n = snn.SNNRecurrent(None, None, 1, 2, MockParams())
    assert (
        str(n)
        == f"SNNRecurrent(input_size=1, hidden_size=2, p={MockParams()}, autapses=False, dt=0.001)"
    )
    n = lif.LIFRecurrent(1, 2, p=LIFParameters())
    assert (
        str(n)
        == f"LIFRecurrent(input_size=1, hidden_size=2, p={LIFParameters()}, autapses=False, dt=0.001)"
    )
