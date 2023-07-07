use std::sync::{Arc, Mutex};

use pyo3::prelude::*;

use tokio::sync::broadcast::{self, Receiver, Sender};

#[pyclass]
#[derive(Clone)]
struct BcastSender {
    sender: Sender<PyObject>,
}

#[pyclass]
struct BcastReceiver {
    receiver: Arc<Mutex<Receiver<PyObject>>>,
    result: Option<Py<PyAny>>,
}

#[pyclass]
struct BcastChannel {
    sender: BcastSender,
}

#[pymethods]
impl BcastChannel {
    #[new]
    fn new() -> Self {
        let (sender, _) = broadcast::channel(16);
        Self {
            sender: BcastSender { sender },
        }
    }

    fn new_sender(&self) -> PyResult<BcastSender> {
        Ok(self.sender.clone())
    }

    fn new_receiver(&self) -> PyResult<BcastReceiver> {
        Ok(BcastReceiver {
            receiver: Arc::new(Mutex::new(self.sender.sender.subscribe())),
            result: None,
        })
    }
}

#[pymethods]
impl BcastSender {
    fn send(&self, py: Python, obj: PyObject) -> PyResult<()> {
        self.sender.send(obj).map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Failed to send message: {}",
                e
            ))
        })?;
        Ok(())
    }
}

async fn receive_impl(recv: Arc<Mutex<Receiver<PyObject>>>) -> PyResult<PyObject> {
    if let Ok(mut receiver) = recv.lock() {
        receiver.recv().await.map_err(|e| {
            PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Failed to receive message: {}",
                e
            ))
        })
    } else {
        Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
            "Failed to lock receiver",
        ))
    }
}

#[pymethods]
impl BcastReceiver {
    fn ready(&mut self, py: Python<'_>) -> PyResult<bool> {
        let recv = self.receiver.clone();
        self.result = Some(
            pyo3_asyncio::tokio::future_into_py(py, async move {
                let result = tokio::task::spawn_blocking(|| {
                    tokio::task::LocalSet::new()
                        .block_on(pyo3_asyncio::tokio::get_runtime(), async move {
                            receive_impl(recv).await
                        })
                });

                result.await.unwrap()
            })
            .unwrap()
            .into_py(py),
        );

        return Ok(true);
    }

    fn consume(&mut self, _py: Python<'_>) -> PyResult<PyObject> {
        if let Some(result) = self.result.take() {
            Ok(result.into())
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(
                "Not ready",
            ))
        }
    }
}

/// A Python module implemented in Rust.
#[pymodule]
fn _channels_impl(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<BcastChannel>()?;
    m.add_class::<BcastSender>()?;
    m.add_class::<BcastReceiver>()?;
    Ok(())
}
