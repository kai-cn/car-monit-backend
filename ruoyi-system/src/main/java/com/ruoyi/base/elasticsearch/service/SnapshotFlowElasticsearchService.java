package com.ruoyi.base.elasticsearch.service;

import com.alibaba.fastjson2.JSON;
import com.ruoyi.base.domain.OdsRtSzdnSnapshotFlowAddcode;
import com.ruoyi.base.elasticsearch.document.SnapshotFlowDocument;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.utils.CommonUtil;
import lombok.extern.slf4j.Slf4j;
import org.elasticsearch.action.bulk.BulkRequest;
import org.elasticsearch.action.bulk.BulkResponse;
import org.elasticsearch.action.index.IndexRequest;
import org.elasticsearch.action.search.SearchRequest;
import org.elasticsearch.action.search.SearchResponse;
import org.elasticsearch.client.RequestOptions;
import org.elasticsearch.client.RestHighLevelClient;
import org.elasticsearch.common.xcontent.XContentType;
import org.elasticsearch.index.query.BoolQueryBuilder;
import org.elasticsearch.index.query.QueryBuilders;
import org.elasticsearch.search.SearchHit;
import org.elasticsearch.search.builder.SearchSourceBuilder;
import org.elasticsearch.search.sort.SortOrder;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

/**
 * Elasticsearch门架抓拍流水服务
 * <p>
 * 用途：提供门架流水数据的ES索引、搜索、批量操作等功能
 * 查询支持：
 * 1. 车牌号：全模糊查询（wildcard）
 * 2. 抓拍时间：范围查询（range）
 * 3. 路段编号/管理中心编号/门架编号：等值查询（term）
 * </p>
 *
 * @author ruoyi
 */
@Slf4j
@Service
public class SnapshotFlowElasticsearchService {

    @Autowired
    private RestHighLevelClient restHighLevelClient;

    /** ES索引名称 */
    @Value("${elasticsearch.index:snapshot-flow}")
    private String indexName;

    /**
     * 保存或更新单条文档到ES
     * <p>
     * 用途：新增或更新单条门架流水记录
     * 使用bigId作为文档ID，实现幂等性
     *
     * @param document ES文档对象
     * @return true=保存成功；false=保存失败
     */
    public boolean saveOrUpdate(SnapshotFlowDocument document) {
        try {
            IndexRequest indexRequest = new IndexRequest(indexName)
                    .id(document.getBigId())
                    .source(JSON.toJSONString(document), XContentType.JSON);
            restHighLevelClient.index(indexRequest, RequestOptions.DEFAULT);
            return true;
        } catch (IOException e) {
            log.error("ES保存文档失败: {}", document.getBigId(), e);
            return false;
        }
    }

    /**
     * 批量保存文档到ES
     * <p>
     * 用途：批量新增或更新门架流水记录，提高性能
     * 使用Bulk API批量提交，减少网络开销
     *
     * @param documents ES文档列表
     * @return true=全部成功；false=部分失败
     */
    public boolean batchSave(List<SnapshotFlowDocument> documents) {
        if (documents == null || documents.isEmpty()) {
            return true;
        }
        try {
            BulkRequest bulkRequest = new BulkRequest();
            for (SnapshotFlowDocument doc : documents) {
                IndexRequest indexRequest = new IndexRequest(indexName)
                        .id(doc.getBigId())
                        .source(JSON.toJSONString(doc), XContentType.JSON);
                bulkRequest.add(indexRequest);
            }
            BulkResponse bulkResponse = restHighLevelClient.bulk(bulkRequest, RequestOptions.DEFAULT);
            return !bulkResponse.hasFailures();
        } catch (IOException e) {
            log.error("ES批量保存文档失败", e);
            return false;
        }
    }

    /**
     * 分页查询ES
     * <p>
     * 用途：根据查询条件从ES中检索门架流水数据
     * 查询条件组合：
     * - platenumber：模糊查询（*xxx*）
     * - sectioncode/orgcode/gantrycode：精确匹配
     * - applyTime1/applyTime2：时间范围
     *
     * @param queryParam 查询参数
     * @return 分页结果，包含数据列表和总数
     */
    public TableDataInfo searchPage(OdsRtSzdnSnapshotFlowAddcode queryParam) {
        TableDataInfo tableDataInfo = new TableDataInfo();
        try {
            SearchRequest searchRequest = new SearchRequest(indexName);
            SearchSourceBuilder sourceBuilder = new SearchSourceBuilder();

            BoolQueryBuilder boolQuery = QueryBuilders.boolQuery();

            if (CommonUtil.isNotBlank(queryParam.getPlatenumber())) {
                boolQuery.must(QueryBuilders.wildcardQuery("platenumber", "*" + queryParam.getPlatenumber() + "*"));
            }

            if (CommonUtil.isNotBlank(queryParam.getSectioncode())) {
                boolQuery.must(QueryBuilders.termQuery("sectioncode", queryParam.getSectioncode()));
            }

            if (CommonUtil.isNotBlank(queryParam.getOrgcode())) {
                boolQuery.must(QueryBuilders.termQuery("orgcode", queryParam.getOrgcode()));
            }

            if (CommonUtil.isNotBlank(queryParam.getGantrycode())) {
                boolQuery.must(QueryBuilders.termQuery("gantrycode", queryParam.getGantrycode()));
            }

            if (CommonUtil.isNotBlank(queryParam.getApplyTime1()) && CommonUtil.isNotBlank(queryParam.getApplyTime2())) {
                boolQuery.must(QueryBuilders.rangeQuery("snapshottime")
                        .gte(queryParam.getApplyTime1())
                        .lte(queryParam.getApplyTime2()));
            }

            sourceBuilder.query(boolQuery);
            sourceBuilder.sort("snapshottime", SortOrder.DESC);

            int pageNum = queryParam.getPageNum() != null ? queryParam.getPageNum() : 1;
            int pageSize = queryParam.getPageSize() != null ? queryParam.getPageSize() : 10;
            sourceBuilder.from((pageNum - 1) * pageSize);
            sourceBuilder.size(pageSize);

            searchRequest.source(sourceBuilder);
            SearchResponse searchResponse = restHighLevelClient.search(searchRequest, RequestOptions.DEFAULT);

            List<OdsRtSzdnSnapshotFlowAddcode> list = new ArrayList<>();
            SearchHit[] hits = searchResponse.getHits().getHits();
            for (SearchHit hit : hits) {
                OdsRtSzdnSnapshotFlowAddcode data = JSON.parseObject(hit.getSourceAsString(), OdsRtSzdnSnapshotFlowAddcode.class);
                list.add(data);
            }

            tableDataInfo.setRows(list);
            tableDataInfo.setTotal(searchResponse.getHits().getTotalHits().value);
            tableDataInfo.setCode(200);
            tableDataInfo.setMsg("查询成功");

        } catch (Exception e) {
            log.error("ES查询失败", e);
            throw new RuntimeException("ES查询失败", e);
        }
        return tableDataInfo;
    }

    /**
     * 检测ES服务是否可用
     * <p>
     * 用途：在查询前检测ES健康状态，决定是否降级到MySQL
     *
     * @return true=ES可用；false=ES不可用
     */
    public boolean isAvailable() {
        try {
            return restHighLevelClient.ping(RequestOptions.DEFAULT);
        } catch (IOException e) {
            log.error("ES连接检测失败", e);
            return false;
        }
    }
}
