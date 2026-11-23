package com.ruoyi.generator.service;

import cn.hutool.core.util.StrUtil;
import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONObject;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.constant.GenConstants;
import com.ruoyi.common.core.text.CharsetKit;
import com.ruoyi.common.exception.CustomException;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.common.utils.file.FileUtils;
import com.ruoyi.generator.domain.*;
import com.ruoyi.generator.mapper.GenTableColumnMapper;
import com.ruoyi.generator.mapper.GenTableMapper;
import com.ruoyi.generator.util.GenUtils;
import com.ruoyi.generator.util.VelocityInitializer;
import com.ruoyi.generator.util.VelocityUtils;
import com.ruoyi.generator.util.enumeration.LinkTableFiledTypeEnum;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.commons.io.IOUtils;
import org.apache.velocity.Template;
import org.apache.velocity.VelocityContext;
import org.apache.velocity.app.Velocity;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.StringWriter;
import java.util.*;
import java.util.stream.Collectors;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

/**
 * 业务 服务层实现
 *
 * @author ruoyi
 */
@Service
public class GenTableServiceImpl implements IGenTableService {
    private static final Logger log = LoggerFactory.getLogger(GenTableServiceImpl.class);
    @Value("${generator-code.mybatis-plus.enable:false}")
    private boolean isMybatisPlus;
    /**
     * 过滤字段列表信息
     */
    private static final List<String> FILTER_COLUMN_NAME_LIST = new ArrayList<>(16);

    @Autowired
    private GenTableMapper genTableMapper;

    @Autowired
    private GenTableColumnMapper genTableColumnMapper;

    @Autowired
    private IGenTableColumnService tableColumnService;

    static {
        FILTER_COLUMN_NAME_LIST.add("sort");
        FILTER_COLUMN_NAME_LIST.add("epsId");
        FILTER_COLUMN_NAME_LIST.add("delFlag");
        FILTER_COLUMN_NAME_LIST.add("tenantId");
    }

    /**
     * 查询业务信息
     *
     * @param id 业务ID
     * @return 业务信息
     */
    @Override
    public GenTable selectGenTableById(Long id) {
        GenTable genTable = genTableMapper.selectGenTableById(id);
        if (genTable == null) {
            return new GenTable();
        }
        setTableFromOptions(genTable);
        return genTable;
    }

    /**
     * 查询业务列表
     *
     * @param genTable 业务信息
     * @return 业务集合
     */
    @Override
    public List<GenTable> selectGenTableList(GenTable genTable) {
        return genTableMapper.selectGenTableList(genTable);
    }

    /**
     * 查询据库列表
     *
     * @param genTable 业务信息
     * @return 数据库表集合
     */
    @Override
    public List<GenTable> selectDbTableList(GenTable genTable) {
        return genTableMapper.selectDbTableList(genTable);
    }

    /**
     * 查询据库列表
     *
     * @param tableNames 表名称组
     * @return 数据库表集合
     */
    @Override
    public List<GenTable> selectDbTableListByNames(String[] tableNames) {
        return genTableMapper.selectDbTableListByNames(tableNames);
    }

    /**
     * 查询所有表信息
     *
     * @return 表信息集合
     */
    @Override
    public List<GenTable> selectGenTableAll() {
        return genTableMapper.selectGenTableAll();
    }

    /**
     * 修改业务
     *
     * @param genTable 业务信息
     * @return 结果
     */
    @Override
    @Transactional
    public void updateGenTable(GenTable genTable) {
        String options = JSON.toJSONString(genTable.getParams());
        genTable.setOptions(options);
        int row = genTableMapper.updateGenTable(genTable);
        if (row > 0) {
            for (GenTableColumn cenTableColumn : genTable.getColumns()) {
                genTableColumnMapper.updateGenTableColumn(cenTableColumn);
            }
        }
    }

    /**
     * 删除业务对象
     *
     * @param tableIds 需要删除的数据ID
     * @return 结果
     */
    @Override
    @Transactional
    public void deleteGenTableByIds(Long[] tableIds) {
        genTableMapper.deleteGenTableByIds(tableIds);
        genTableColumnMapper.deleteGenTableColumnByIds(tableIds);
    }

    /**
     * 导入表结构
     *
     * @param tableList 导入表列表
     */
    @Override
    @Transactional
    public void importGenTable(List<GenTable> tableList) {
        String operName = SecurityUtils.getUsername();
        try {
            for (GenTable table : tableList) {
                String tableName = table.getTableName();
                GenUtils.initTable(table, operName);
                int row = genTableMapper.insertGenTable(table);
                if (row > 0) {
                    // 保存列信息
                    List<GenTableColumn> genTableColumns = genTableColumnMapper.selectDbTableColumnsByName(tableName);
                    for (GenTableColumn column : genTableColumns) {
                        GenUtils.initColumnField(column, table);
                        genTableColumnMapper.insertGenTableColumn(column);
                    }
                }
            }
        } catch (Exception e) {
            throw new CustomException("导入失败：" + e.getMessage());
        }
    }

    /**
     * 预览代码
     *
     * @param tableId 表编号
     * @return 预览数据列表
     */
    @Override
    public Map<String, String> previewCode(Long tableId) {
        Map<String, String> dataMap = new LinkedHashMap<>();
        // 查询表信息
        GenTable table = genTableMapper.selectGenTableById(tableId);
        if (table == null) {
            return dataMap;
        }
        // 过滤字段信息
        this.initFilterColumnInfo(table);
        // 初始化富文本信息
        this.initRichTextInfo(table);
        // 初始化附件上传信息
        this.initUploadInfo(table);
        // 将字典的key转换成驼峰类型
        this.dictionaryKeyToCamelCase(table);
        // 初始化关联表信息
        this.initLinkTableInfo(table);

        // 设置主子表信息
        setSubTable(table);
        // 设置主键列信息
        setPkColumn(table);
        VelocityInitializer.initVelocity();

        VelocityContext context = VelocityUtils.prepareContext(table);

        // 获取模板列表
        List<String> templates = VelocityUtils.getTemplateList(table.getTplCategory(),isMybatisPlus);
        for (String template : templates) {
            // 渲染模板
            StringWriter sw = new StringWriter();
            Template tpl = Velocity.getTemplate(template, Constants.UTF8);
            tpl.merge(context, sw);
            dataMap.put(template, sw.toString());
        }
        return dataMap;
    }

    /**
     * 生成代码（下载方式）
     *
     * @param tableName 表名称
     * @return 数据
     */
    @Override
    public byte[] downloadCode(String tableName) {
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        ZipOutputStream zip = new ZipOutputStream(outputStream);
        generatorCode(tableName, zip);
        IOUtils.closeQuietly(zip);
        return outputStream.toByteArray();
    }

    /**
     * 生成代码（自定义路径）
     *
     * @param tableName 表名称
     */
    @Override
    public void generatorCode(String tableName) {
        // 查询表信息
        GenTable table = genTableMapper.selectGenTableByName(tableName);
        if (table == null) {
            return;
        }
        // 将字典的key转换成驼峰类型
        this.dictionaryKeyToCamelCase(table);
        // 初始化富文本信息
        this.initRichTextInfo(table);
        // 过滤字段信息
        this.initFilterColumnInfo(table);
        // 初始化关联表信息
        this.initLinkTableInfo(table);
        // 初始化附件上传信息
        this.initUploadInfo(table);

        // 设置主子表信息
        setSubTable(table);
        // 设置主键列信息
        setPkColumn(table);
        VelocityInitializer.initVelocity();

        VelocityContext context = VelocityUtils.prepareContext(table);

        // 获取模板列表
        List<String> templates = VelocityUtils.getTemplateList(table.getTplCategory(),isMybatisPlus);
        for (String template : templates) {
            if (!StringUtils.containsAny(template, "sql.vm", "api.js.vm", "index.vue.vm", "index-tree.vue.vm")) {
                // 渲染模板
                StringWriter sw = new StringWriter();
                Template tpl = Velocity.getTemplate(template, Constants.UTF8);
                tpl.merge(context, sw);
                try {
                    String path = getGenPath(table, template);
                    FileUtils.writeStringToFile(new File(path), sw.toString(), CharsetKit.UTF_8);
                } catch (IOException e) {
                    throw new CustomException("渲染模板失败，表名：" + table.getTableName());
                }
            }
        }
    }

    /**
     * 同步数据库
     *
     * @param tableName 表名称
     */
    @Override
    @Transactional
    public void synchDb(String tableName) {
        GenTable table = genTableMapper.selectGenTableByName(tableName);
        if (table == null) {
            return;
        }
        List<GenTableColumn> tableColumns = table.getColumns();
        List<String> tableColumnNames = tableColumns.stream().map(GenTableColumn::getColumnName).collect(Collectors.toList());

        List<GenTableColumn> dbTableColumns = genTableColumnMapper.selectDbTableColumnsByName(tableName);
        if (StringUtils.isEmpty(dbTableColumns)) {
            throw new CustomException("同步数据失败，原表结构不存在");
        }
        List<String> dbTableColumnNames = dbTableColumns.stream().map(GenTableColumn::getColumnName).collect(Collectors.toList());

        dbTableColumns.forEach(column -> {
            if (!tableColumnNames.contains(column.getColumnName())) {
                GenUtils.initColumnField(column, table);
                genTableColumnMapper.insertGenTableColumn(column);
            }
        });

        List<GenTableColumn> delColumns = tableColumns.stream().filter(column -> !dbTableColumnNames.contains(column.getColumnName())).collect(Collectors.toList());
        if (StringUtils.isNotEmpty(delColumns)) {
            genTableColumnMapper.deleteGenTableColumns(delColumns);
        }
    }

    /**
     * 批量生成代码（下载方式）
     *
     * @param tableNames 表数组
     * @return 数据
     */
    @Override
    public byte[] downloadCode(String[] tableNames) {
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        ZipOutputStream zip = new ZipOutputStream(outputStream);
        for (String tableName : tableNames) {
            generatorCode(tableName, zip);
        }
        IOUtils.closeQuietly(zip);
        return outputStream.toByteArray();
    }

    /**
     * 查询表信息并生成代码
     */
    private void generatorCode(String tableName, ZipOutputStream zip) {
        // 查询表信息
        GenTable table = genTableMapper.selectGenTableByName(tableName);
        if (table == null) {
            return;
        }
        // 将字典的key转换成驼峰类型
        this.dictionaryKeyToCamelCase(table);
        // 初始化附件上传信息
        this.initUploadInfo(table);
        // 初始化富文本信息
        this.initRichTextInfo(table);
        // 初始化关联表信息
        this.initLinkTableInfo(table);
        // 过滤字段信息
        this.initFilterColumnInfo(table);

        // 设置主子表信息
        setSubTable(table);
        // 设置主键列信息
        setPkColumn(table);
        VelocityInitializer.initVelocity();

        VelocityContext context = VelocityUtils.prepareContext(table);

        // 获取模板列表
        List<String> templates = VelocityUtils.getTemplateList(table.getTplCategory(),isMybatisPlus);
        for (String template : templates) {
            // 渲染模板
            StringWriter sw = new StringWriter();
            Template tpl = Velocity.getTemplate(template, Constants.UTF8);
            tpl.merge(context, sw);
            try {
                // 添加到zip
                zip.putNextEntry(new ZipEntry(VelocityUtils.getFileName(template, table)));
                IOUtils.write(sw.toString(), zip, Constants.UTF8);
                IOUtils.closeQuietly(sw);
                zip.flush();
                zip.closeEntry();
            } catch (IOException e) {
                log.error("渲染模板失败，表名：" + table.getTableName(), e);
            }
        }
    }

    /**
     * 初始化附件上传信息
     *
     * @param table
     */
    private void initUploadInfo(GenTable table) {
        List<GenTableColumn> columnList = table.getColumns();
        if (CollectionUtils.isNotEmpty(columnList)) {
            List<GenTableColumn> uploadColumnList = columnList.stream().filter(column -> "fileUpload".equals(column.getHtmlType())).collect(Collectors.toList());
            GenerateUploadInfo generateUploadInfo = new GenerateUploadInfo();
            if (CollectionUtils.isNotEmpty(uploadColumnList)) {
                List<String> javaFieldNameList = uploadColumnList.stream().map(GenTableColumn::getJavaField).collect(Collectors.toList());

                generateUploadInfo.setUploadCount(uploadColumnList.size())
                        .setUploadColumn(uploadColumnList)
                        .setUploadFiledNames(StringUtils.join(javaFieldNameList, StrUtil.COMMA));
            } else {
                generateUploadInfo.setUploadCount(0);
            }

            table.setUploadInfo(generateUploadInfo);
        }
    }

    /**
     * 初始化富文本信息
     *
     * @param table
     */
    private void initRichTextInfo(GenTable table) {
        List<GenTableColumn> columnList = table.getColumns();
        if (CollectionUtils.isNotEmpty(columnList)) {
            List<GenTableColumn> richTextColumnList = columnList.stream().filter(column -> "editor".equals(column.getHtmlType())).collect(Collectors.toList());
            GenerateRichTextInfo generateRichTextInfo = new GenerateRichTextInfo();
            if (CollectionUtils.isNotEmpty(richTextColumnList)) {
                generateRichTextInfo.setRichTextCount(richTextColumnList.size())
                        .setColumnList(richTextColumnList);
            } else {
                generateRichTextInfo.setRichTextCount(0);
            }

            table.setRichTextInfo(generateRichTextInfo);
        }
    }

    /**
     * 初始化关联表信息
     *
     * @param genTable
     */
    private void initLinkTableInfo(GenTable genTable) {
        List<GenTableColumn> columnList = genTable.getColumns();
        if (CollectionUtils.isNotEmpty(columnList)) {
            // 关联表信息列表
            List<GenTableColumn> linkTableColumnList = columnList.stream()
                    .filter(column -> column.getLinkTableId() != null && StringUtils.isNotBlank(column.getFieldMapString()))
                    .collect(Collectors.toList());

            // 初始化对话框查询显示列表数据信息
            this.initDialogQueryShowData(linkTableColumnList);

            // 多选对话框列表
            List<GenTableColumn> checkboxColumnList = new ArrayList<>(16);
            // 单选对话框列表
            List<GenTableColumn> radioColumnList = new ArrayList<>(16);

            // 全部字段列表
            List<LinkTableField> allFieldList = new ArrayList<>(16);
            // 全部自定义字段列表
            List<LinkTableField> allCustomFieldList = new ArrayList<>(16);
            // 全部表中字段列表
            List<LinkTableField> allTableFieldList = new ArrayList<>(16);

            // 初始化关联字段信息
            linkTableColumnList.forEach(column -> {
                // 单选对话框
                if ("1".equals(column.getSingleSelection())) {
                    radioColumnList.add(column);
                }

                // 多选对话框
                if ("1".equals(column.getMultipleSelections())) {
                    checkboxColumnList.add(column);
                }

                // 字段映射
                String fieldMapString = column.getFieldMapString();
                List<LinkTableField> linkTableFieldList = JSON.parseArray(fieldMapString, LinkTableField.class);

                List<LinkTableField> tableFieldList = linkTableFieldList.stream().filter(fieldInfo -> LinkTableFiledTypeEnum.TABLE.getCode().equals(fieldInfo.getFieldType())).collect(Collectors.toList());
                List<LinkTableField> customFieldList = linkTableFieldList.stream().filter(fieldInfo -> LinkTableFiledTypeEnum.CUSTOM_FIELD.getCode().equals(fieldInfo.getFieldType())).collect(Collectors.toList());

                if (CollectionUtils.isNotEmpty(tableFieldList)) {
                    column.setTableFieldList(tableFieldList);

                    allTableFieldList.addAll(tableFieldList);
                    allFieldList.addAll(tableFieldList);
                }

                if (CollectionUtils.isNotEmpty(customFieldList)) {
                    column.setCustomFieldList(customFieldList);

                    allCustomFieldList.addAll(customFieldList);
                    allFieldList.addAll(customFieldList);
                }

                // 设置生成关联表标识
                column.setGenerateLinkTableFlag("1");
                // 设置字段主要映射关系
                Optional<LinkTableField> majorLinkFieldInfo = tableFieldList.stream().filter(data -> Objects.equals(column.getColumnId(), data.getCurrentTableFileId())).findFirst();
                column.setMajorLinkFieldInfo(majorLinkFieldInfo.get());
            });

            // 设置表字段信息
            this.initTableFieldInfo(allTableFieldList);
            // 设置关联表字段信息
            this.initLinkTableFieldInfo(allFieldList);

            // 设置对话框信息
            GenColumnDialog columnDialog = new GenColumnDialog();
            columnDialog.setDialogColumnList(linkTableColumnList);
            if (CollectionUtils.isNotEmpty(linkTableColumnList)) {
                columnDialog.setDialogNumber(linkTableColumnList.size());
            } else {
                columnDialog.setDialogNumber(0);
            }

            // 设置多选对话框信息
            columnDialog.setCheckBoxColumnList(checkboxColumnList);
            if (CollectionUtils.isNotEmpty(checkboxColumnList)) {
                columnDialog.setCheckboxNumber(checkboxColumnList.size());
            } else {
                columnDialog.setCheckboxNumber(0);
            }

            // 设置单选对话框信息
            columnDialog.setRadioColumnList(radioColumnList);
            if (CollectionUtils.isNotEmpty(radioColumnList)) {
                columnDialog.setRadioNumber(radioColumnList.size());
            } else {
                columnDialog.setRadioNumber(0);
            }

            // 设置全部-表字段信息
            columnDialog.setTableFieldList(allTableFieldList);
            // 设置全部-自定义字段信息
            columnDialog.setCustomFieldList(allCustomFieldList);
            // 设置全部-字段信息
            columnDialog.setFieldList(allFieldList);

            // 设置字段对话框信息
            genTable.setColumnDialogInfo(columnDialog);
        }
    }

    /**
     * 设置表字段信息
     *
     * @param allTableFieldList
     */
    private void initTableFieldInfo(List<LinkTableField> allTableFieldList) {
        if (CollectionUtils.isEmpty(allTableFieldList)) {
            return;
        }

        // 获取表字段信息
        List<Long> tableIdList = allTableFieldList.stream().map(LinkTableField::getCurrentTableFileId).collect(Collectors.toList());
        List<GenTableColumn> tableColumnList = tableColumnService.selectGenTableColumnListByTableColumnIdList(tableIdList);
        if (CollectionUtils.isNotEmpty(tableColumnList)) {
            // 缓存表字段信息map
            Map<Long, GenTableColumn> tableColumnMap = tableColumnList.stream().collect(Collectors.toMap(GenTableColumn::getColumnId, data -> data));
            // 添加表字段信息
            allTableFieldList.forEach(fieldInfo -> {
                GenTableColumn genTableColumn = tableColumnMap.get(fieldInfo.getCurrentTableFileId());
                if (genTableColumn != null) {
                    fieldInfo.setTableFileInfo(genTableColumn);
                }
            });
        }
    }

    /**
     * 初始化关联表字段信息
     *
     * @param allFieldList
     */
    private void initLinkTableFieldInfo(List<LinkTableField> allFieldList) {
        if (CollectionUtils.isEmpty(allFieldList)) {
            return;
        }

        List<Long> linkFieldIdList = allFieldList.stream().map(LinkTableField::getLinkTableFieldId).collect(Collectors.toList());
        List<GenTableColumn> linkFieldList = tableColumnService.selectGenTableColumnListByTableColumnIdList(linkFieldIdList);
        if (CollectionUtils.isNotEmpty(linkFieldList)) {
            // 缓存表字段信息map
            Map<Long, GenTableColumn> columnMap = linkFieldList.stream().collect(Collectors.toMap(GenTableColumn::getColumnId, data -> data));
            // 添加表字段信息
            allFieldList.forEach(fieldInfo -> {
                GenTableColumn genTableColumn = columnMap.get(fieldInfo.getLinkTableFieldId());
                if (genTableColumn != null) {
                    fieldInfo.setLinkTableFieldInfo(genTableColumn);
                }
            });
        }
    }

    /**
     * 初始化对话框查询显示列表数据信息
     *
     * @param linkTableColumnList
     */
    private void initDialogQueryShowData(List<GenTableColumn> linkTableColumnList) {
        if (CollectionUtils.isEmpty(linkTableColumnList)) {
            return;
        }

        linkTableColumnList.forEach(column -> {
            String dialogSearchColumnIds = column.getDialogSearchColumnIds();
            String dialogListColumnIds = column.getDialogListColumnIds();
            Long linkTableId = column.getLinkTableId();

            // dialog查询字段信息
            if (StringUtils.isNotEmpty(dialogSearchColumnIds)) {
                List<GenTableColumn> searchColumnList = tableColumnService.selectGenTableColumnListByTableColumnIds(dialogSearchColumnIds);
                column.setDialogSearchColumnList(searchColumnList);
            }

            // dialog展示字段信息
            if (StringUtils.isNotEmpty(dialogListColumnIds)) {
                List<GenTableColumn> showColumnList = tableColumnService.selectGenTableColumnListByTableColumnIds(dialogListColumnIds);
                column.setDialogShowColumnList(showColumnList);
            }

            // 关联表信息
            GenTable linkTable = genTableMapper.selectGenTableById(linkTableId);
            // 设置主键列信息
            setPkColumn(linkTable);
            column.setLinkTable(linkTable);
        });
    }

    /**
     * 过滤字段信息
     *
     * @param genTable
     */
    private void initFilterColumnInfo(GenTable genTable) {
        List<GenTableColumn> columnList = genTable.getColumns();
        if (CollectionUtils.isEmpty(columnList)) {
            return;
        }

        List<GenTableColumn> filterColumnList = columnList.stream().filter(column -> {
            if (StringUtils.isEmpty(column.getJavaField())) {
                return false;
            }

            // 过滤id为String类型的字段
            if (Constants.COLUMN_PRIMARY_KEY.equals(column.getJavaField()) &&
                    Constants.STRING_CLASS_KEY.equals(column.getJavaType())) {

                return false;
            }

            if (FILTER_COLUMN_NAME_LIST.contains(column.getJavaField())) {
                return false;
            }

            return true;
        }).collect(Collectors.toList());

        // 设置已过滤字段信息
        genTable.setFilterColumnList(filterColumnList);
    }

    /**
     * 修改保存参数校验
     *
     * @param genTable 业务信息
     */
    @Override
    public void validateEdit(GenTable genTable) {
        if (GenConstants.TPL_TREE.equals(genTable.getTplCategory())) {
            String options = JSON.toJSONString(genTable.getParams());
            JSONObject paramsObj = JSONObject.parseObject(options);
            if (StringUtils.isEmpty(paramsObj.getString(GenConstants.TREE_CODE))) {
                throw new CustomException("树编码字段不能为空");
            } else if (StringUtils.isEmpty(paramsObj.getString(GenConstants.TREE_PARENT_CODE))) {
                throw new CustomException("树父编码字段不能为空");
            } else if (StringUtils.isEmpty(paramsObj.getString(GenConstants.TREE_NAME))) {
                throw new CustomException("树名称字段不能为空");
            } else if (GenConstants.TPL_SUB.equals(genTable.getTplCategory())) {
                if (StringUtils.isEmpty(genTable.getSubTableName())) {
                    throw new CustomException("关联子表的表名不能为空");
                } else if (StringUtils.isEmpty(genTable.getSubTableFkName())) {
                    throw new CustomException("子表关联的外键名不能为空");
                }
            }
        }
    }

    /**
     * 设置主键列信息
     *
     * @param table 业务表信息
     */
    public void setPkColumn(GenTable table) {
        for (GenTableColumn column : table.getColumns()) {
            if (column.isPk()) {
                table.setPkColumn(column);
                break;
            }
        }
        if (StringUtils.isNull(table.getPkColumn())) {
            table.setPkColumn(table.getColumns().get(0));
        }
        if (GenConstants.TPL_SUB.equals(table.getTplCategory())) {
            for (GenTableColumn column : table.getSubTable().getColumns()) {
                if (column.isPk()) {
                    table.getSubTable().setPkColumn(column);
                    break;
                }
            }
            if (StringUtils.isNull(table.getSubTable().getPkColumn())) {
                table.getSubTable().setPkColumn(table.getSubTable().getColumns().get(0));
            }
        }
    }

    /**
     * 设置主子表信息
     *
     * @param table 业务表信息
     */
    public void setSubTable(GenTable table) {
        String subTableName = table.getSubTableName();
        if (StringUtils.isNotEmpty(subTableName)) {
            table.setSubTable(genTableMapper.selectGenTableByName(subTableName));
        }
    }

    /**
     * 设置代码生成其他选项值
     *
     * @param genTable 设置后的生成对象
     */
    public void setTableFromOptions(GenTable genTable) {
        JSONObject paramsObj = JSONObject.parseObject(genTable.getOptions());
        if (StringUtils.isNotNull(paramsObj)) {
            String treeCode = paramsObj.getString(GenConstants.TREE_CODE);
            String treeParentCode = paramsObj.getString(GenConstants.TREE_PARENT_CODE);
            String treeName = paramsObj.getString(GenConstants.TREE_NAME);
            String parentMenuId = paramsObj.getString(GenConstants.PARENT_MENU_ID);
            String parentMenuName = paramsObj.getString(GenConstants.PARENT_MENU_NAME);

            genTable.setTreeCode(treeCode);
            genTable.setTreeParentCode(treeParentCode);
            genTable.setTreeName(treeName);
            genTable.setParentMenuId(parentMenuId);
            genTable.setParentMenuName(parentMenuName);
        }
    }

    /**
     * 将字典的key转换成驼峰类型
     *
     * @param table
     */
    private void dictionaryKeyToCamelCase(GenTable table) {
        if (table != null && CollectionUtils.isNotEmpty(table.getColumns())) {
            List<GenTableColumn> columnList = table.getColumns();
            List<DictionaryInfo> dictionaryInfoList = new ArrayList<>();
            columnList.stream().filter(column -> StringUtils.isNotEmpty(column.getDictType())).forEach(column -> {
                String dictTypeCamelCase = StringUtils.toCamelCase(column.getDictType());
                column.setDictTypeCamelCase(dictTypeCamelCase);

                DictionaryInfo dictionaryInfo = new DictionaryInfo();
                dictionaryInfo.setDictionaryKey(column.getDictType()).setDictionaryKeyCamelCase(dictTypeCamelCase);
                dictionaryInfoList.add(dictionaryInfo);
            });

            // 设置字典信息
            if (CollectionUtils.isNotEmpty(dictionaryInfoList)) {
                table.setDictionaryInfoList(dictionaryInfoList);
                List<String> dictKeyList = dictionaryInfoList.stream().map(DictionaryInfo::getDictionaryKey).collect(Collectors.toList());
                table.setDictionaryInfoString(StringUtils.join(dictKeyList, StrUtil.COMMA));
            }

            // 设置 生成代码-字典列表键后缀
            table.setDictionaryListKeySuffix(Constants.GENERATE_CODE_DICTIONARY_LIST_KEY_SUFFIX);
        }
    }

    /**
     * 获取代码生成地址
     *
     * @param table    业务表信息
     * @param template 模板文件路径
     * @return 生成地址
     */
    public static String getGenPath(GenTable table, String template) {
        String genPath = table.getGenPath();
        if (StringUtils.equals(genPath, "/")) {
            return System.getProperty("user.dir") + File.separator + "src" + File.separator + VelocityUtils.getFileName(template, table);
        }
        return genPath + File.separator + VelocityUtils.getFileName(template, table);
    }
}
