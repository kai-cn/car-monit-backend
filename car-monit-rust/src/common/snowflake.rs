// 来源: ruoyi-common/src/main/java/com/ruoyi/common/utils/SnowflakeIdWorker.java
//       ruoyi-common/src/main/java/com/ruoyi/common/config/IdWorkerConfig.java
// 职责: 与 Java 同算法的 64 位雪花 ID（twepoch 2015-01-01，worker/datacenter 各 5 位，序列 12 位）。
// 对应关系: IdWorkerConfig.snowflakeIdWorker() 单例 -> AppState.snowflake。

use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

use crate::error::AppError;

const TWEPOCH: i64 = 1_420_041_600_000;
const WORKER_ID_BITS: i64 = 5;
const DATACENTER_ID_BITS: i64 = 5;
const SEQUENCE_BITS: i64 = 12;
const MAX_WORKER_ID: i64 = -1 ^ (-1 << WORKER_ID_BITS);
const MAX_DATACENTER_ID: i64 = -1 ^ (-1 << DATACENTER_ID_BITS);
const WORKER_ID_SHIFT: i64 = SEQUENCE_BITS;
const DATACENTER_ID_SHIFT: i64 = SEQUENCE_BITS + WORKER_ID_BITS;
const TIMESTAMP_SHIFT: i64 = SEQUENCE_BITS + WORKER_ID_BITS + DATACENTER_ID_BITS;
const SEQUENCE_MASK: i64 = -1 ^ (-1 << SEQUENCE_BITS);

struct SnowflakeState {
    last_timestamp: i64,
    sequence: i64,
}

pub struct SnowflakeIdWorker {
    worker_id: i64,
    datacenter_id: i64,
    state: Mutex<SnowflakeState>,
}

impl SnowflakeIdWorker {
    /// Java: `new SnowflakeIdWorker(workerId, datacenterId)`；越界抛 IllegalArgumentException。
    pub fn new(worker_id: i64, datacenter_id: i64) -> Result<Self, AppError> {
        if !(0..=MAX_WORKER_ID).contains(&worker_id) {
            return Err(AppError::internal(format!(
                "worker Id can't be greater than {MAX_WORKER_ID} or less than 0"
            )));
        }
        if !(0..=MAX_DATACENTER_ID).contains(&datacenter_id) {
            return Err(AppError::internal(format!(
                "datacenter Id can't be greater than {MAX_DATACENTER_ID} or less than 0"
            )));
        }
        Ok(Self {
            worker_id,
            datacenter_id,
            state: Mutex::new(SnowflakeState {
                last_timestamp: -1,
                sequence: 0,
            }),
        })
    }

    /// Java: `synchronized long nextId()`；时钟回拨时抛 RuntimeException。
    pub fn next_id(&self) -> Result<i64, AppError> {
        let mut state = self
            .state
            .lock()
            .map_err(|_| AppError::internal("雪花 ID 锁已中毒"))?;
        let mut timestamp = time_gen();

        if timestamp < state.last_timestamp {
            return Err(AppError::Service(format!(
                "Clock moved backwards.  Refusing to generate id for {} milliseconds",
                state.last_timestamp - timestamp
            )));
        }

        if state.last_timestamp == timestamp {
            state.sequence = (state.sequence + 1) & SEQUENCE_MASK;
            if state.sequence == 0 {
                timestamp = til_next_millis(state.last_timestamp);
            }
        } else {
            state.sequence = 0;
        }

        state.last_timestamp = timestamp;
        Ok(((timestamp - TWEPOCH) << TIMESTAMP_SHIFT)
            | (self.datacenter_id << DATACENTER_ID_SHIFT)
            | (self.worker_id << WORKER_ID_SHIFT)
            | state.sequence)
    }
}

fn til_next_millis(last_timestamp: i64) -> i64 {
    let mut timestamp = time_gen();
    while timestamp <= last_timestamp {
        timestamp = time_gen();
    }
    timestamp
}

fn time_gen() -> i64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_millis() as i64)
        .unwrap_or(0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_out_of_range_ids() {
        assert!(SnowflakeIdWorker::new(32, 0).is_err());
        assert!(SnowflakeIdWorker::new(0, -1).is_err());
    }

    #[test]
    fn ids_are_monotonic_and_contain_worker_bits() {
        let worker = SnowflakeIdWorker::new(3, 5).expect("worker");
        let mut previous = 0;
        for _ in 0..1000 {
            let id = worker.next_id().expect("id");
            assert!(id > previous);
            previous = id;
            assert_eq!((id >> WORKER_ID_SHIFT) & MAX_WORKER_ID, 3);
            assert_eq!((id >> DATACENTER_ID_SHIFT) & MAX_DATACENTER_ID, 5);
        }
    }
}
