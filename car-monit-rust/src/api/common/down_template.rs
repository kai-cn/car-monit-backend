// 来源: ruoyi-admin/src/main/java/com/ruoyi/web/controller/common/DownTemplateController.java
// 职责: 按 type 下载导入模板（config/templates/down/*.xlsx）。
// 对应关系: EasyPOI TemplateExportParams(url) -> 直接返回模板字节（附件，无 filename）。

use axum::extract::Path;
use axum::http::header;
use axum::response::{IntoResponse, Response};
use axum::Router;

use crate::api::meta;
use crate::state::AppState;

pub fn routes() -> Router<AppState> {
    Router::new().route(
        "/downTemplate/{type}",
        meta::get_route("/downTemplate/{type}", None, None, download),
    )
}

async fn download(Path(template_type): Path<String>) -> Response {
    let file = match template_type.as_str() {
        "goodsFkApplyDetail" => "importGoodsFkApplyDetail.xlsx",
        "goodsRkApplyDetail" => "importGoodsRkApplyDetail.xlsx",
        "planListDetail" => "importPlanListDetail.xlsx",
        "importPsbz" => "importPsbz.xlsx",
        "importSupplierAnnualScore" => "importSupplierAnnualScore.xlsx",
        "carinfo" => "importCar.xlsx",
        "carExcept" => "importCarExcept.xlsx",
        _ => "down",
    };
    let path = std::path::PathBuf::from("config/templates/down").join(file);
    match std::fs::read(&path) {
        Ok(bytes) => (
            [
                (
                    header::CONTENT_TYPE,
                    "application/octet-stream;charset=UTF-8".to_string(),
                ),
                (header::CONTENT_DISPOSITION, "attachment".to_string()),
            ],
            bytes,
        )
            .into_response(),
        Err(err) => {
            tracing::error!("模板下载失败 {}: {err}", path.display());
            ([(header::CONTENT_TYPE, "application/octet-stream")], Vec::<u8>::new())
                .into_response()
        }
    }
}
