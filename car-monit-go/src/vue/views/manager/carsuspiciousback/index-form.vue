<template>
    <div>
        <el-form ref="form" :model="form" :rules="rules" label-width="auto" id="form" @submit.native.prevent >
          <template v-if="!datFromDisabled">
            <el-row :gutter="20">
                                <el-col :span="12">
                                    <el-form-item label="车牌颜色（字典：1白色2黑色）" prop="plateColor">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.plateColor" placeholder="请输入车牌颜色（字典：1白色2黑色）" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="车牌号" prop="carNo">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.carNo" placeholder="请输入车牌号" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="车型" prop="carType">
                                            <el-select  style="width:100%;"   :disabled="datFromDisabled" v-model="form.carType" :clearable="true" filterable placeholder="请选择车型">
                                                <el-option v-for="(item, index) in $column.dictTypeCamelCaseDictList" :key="index" :label="item.dictLabel" :value="item.dictValue">
                                                </el-option>
                                            </el-select>
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="车种" prop="carVehicle">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.carVehicle" placeholder="请输入车种" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="轴数" prop="carNum">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.carNum" placeholder="请输入轴数" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="通行标识（1人工2ETC）" prop="passType">
                                            <el-select  style="width:100%;"   :disabled="datFromDisabled" v-model="form.passType" :clearable="true" filterable placeholder="请选择通行标识（1人工2ETC）">
                                                <el-option v-for="(item, index) in $column.dictTypeCamelCaseDictList" :key="index" :label="item.dictLabel" :value="item.dictValue">
                                                </el-option>
                                            </el-select>
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="入口站id" prop="inStationId">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.inStationId" placeholder="请输入入口站id" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="入口站" prop="inStation">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.inStation" placeholder="请输入入口站" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="通行时间" prop="inTime">
                                            <el-date-picker  style="width:100%;"   :disabled="datFromDisabled" v-model="form.inTime" type="date" value-format="yyyy-MM-dd" placement="bottom-start" placeholder="通行时间">
                                            </el-date-picker>
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="出口站id" prop="outStationId">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.outStationId" placeholder="请输入出口站id" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="出口站" prop="outStation">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.outStation" placeholder="请输入出口站" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="出口时间" prop="outTime">
                                            <el-date-picker  style="width:100%;"   :disabled="datFromDisabled" v-model="form.outTime" type="date" value-format="yyyy-MM-dd" placement="bottom-start" placeholder="出口时间">
                                            </el-date-picker>
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="门架id" prop="gantryStationId">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.gantryStationId" placeholder="请输入门架id" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="门架名称" prop="gantrytStation">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.gantrytStation" placeholder="请输入门架名称" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="经过时间" prop="gantryTime">
                                            <el-date-picker  style="width:100%;"   :disabled="datFromDisabled" v-model="form.gantryTime" type="date" value-format="yyyy-MM-dd" placement="bottom-start" placeholder="经过时间">
                                            </el-date-picker>
                                    </el-form-item>
                                </el-col>
                                <el-col :span="24">
                                    <el-form-item label="图片(附件ids)" prop="fileIds">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.fileIds" type="textarea" :autosize="{minRows:2}" placeholder="请输入图片(附件ids)" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="终止门架id" prop="outGantryStationId">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.outGantryStationId" placeholder="请输入终止门架id" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="终止门架名称" prop="outGantrytStation">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.outGantrytStation" placeholder="请输入终止门架名称" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="终止经过时间" prop="outGantryTime">
                                            <el-date-picker  style="width:100%;"   :disabled="datFromDisabled" v-model="form.outGantryTime" type="date" value-format="yyyy-MM-dd" placement="bottom-start" placeholder="终止经过时间">
                                            </el-date-picker>
                                    </el-form-item>
                                </el-col>
                                <el-col :span="24">
                                    <el-form-item label="终止图片(附件ids)" prop="outFileIds">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.outFileIds" type="textarea" :autosize="{minRows:2}" placeholder="请输入终止图片(附件ids)" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）" prop="escapedType">
                                            <el-select  style="width:100%;"   :disabled="datFromDisabled" v-model="form.escapedType" :clearable="true" filterable placeholder="请选择逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）">
                                                <el-option v-for="(item, index) in $column.dictTypeCamelCaseDictList" :key="index" :label="item.dictLabel" :value="item.dictValue">
                                                </el-option>
                                            </el-select>
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="逃费类型名称" prop="escapedTypeName">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.escapedTypeName" placeholder="请输入逃费类型名称" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="异常通行门架次数" prop="escapedNum">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.escapedNum" placeholder="请输入异常通行门架次数" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="是否为可疑车辆" prop="isExcept">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.isExcept" placeholder="请输入是否为可疑车辆" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="24">
                                    <el-form-item label="可疑原因" prop="exceptRemark">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.exceptRemark" type="textarea" :autosize="{minRows:2}" placeholder="请输入可疑原因" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="24">
                                    <el-form-item label="可疑材料" prop="exceptFileIds">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.exceptFileIds" type="textarea" :autosize="{minRows:2}" placeholder="请输入可疑材料" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="核实状态（0未核实1已核实）" prop="checkStatus">
                                            <el-select  style="width:100%;"   :disabled="datFromDisabled" v-model="form.checkStatus" :clearable="true" filterable placeholder="请选择核实状态（0未核实1已核实）">
                                                <el-option v-for="(item, index) in $column.dictTypeCamelCaseDictList" :key="index" :label="item.dictLabel" :value="item.dictValue">
                                                </el-option>
                                            </el-select>
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="管理中心id" prop="orgId">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.orgId" placeholder="请输入管理中心id" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="管理中心名称" prop="orgName">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.orgName" placeholder="请输入管理中心名称" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="是否在白名单（0否1是）" prop="isWhite">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.isWhite" placeholder="请输入是否在白名单（0否1是）" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="24">
                                    <el-form-item label="白名单原因" prop="whiteRemark">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.whiteRemark" type="textarea" :autosize="{minRows:2}" placeholder="请输入白名单原因" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="24">
                                    <el-form-item label="白名单材料" prop="whiteFileIds">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.whiteFileIds" type="textarea" :autosize="{minRows:2}" placeholder="请输入白名单材料" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="所属路线编码" prop="roadCode">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.roadCode" placeholder="请输入所属路线编码" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="所属路线名称" prop="roadName">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.roadName" placeholder="请输入所属路线名称" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="所属路段编码" prop="sectionCode">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.sectionCode" placeholder="请输入所属路段编码" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="所属路段名称" prop="sectionName">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.sectionName" placeholder="请输入所属路段名称" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="行驶轨迹id" prop="trackId">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.trackId" placeholder="请输入行驶轨迹id" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="24">
                                    <el-form-item label="行驶轨迹josn" prop="trackJosn">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.trackJosn" type="textarea" :autosize="{minRows:2}" placeholder="请输入行驶轨迹josn" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="24">
                                    <el-form-item label="轨迹点集合" prop="trackNames">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.trackNames" type="textarea" :autosize="{minRows:2}" placeholder="请输入轨迹点集合" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="备用字段1" prop="backCol1">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.backCol1" placeholder="请输入备用字段1" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="12">
                                    <el-form-item label="备用字段2" prop="backCol2">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.backCol2" placeholder="请输入备用字段2" />
                                    </el-form-item>
                                </el-col>
                                <el-col :span="24">
                                    <el-form-item label="备注" prop="remark">
                                            <el-input  style="width:100%;"   :disabled="datFromDisabled" v-model="form.remark" type="textarea" :autosize="{minRows:2}" placeholder="请输入备注" />
                                    </el-form-item>
                                </el-col>
            </el-row>
          </template>
            <template v-else>
                <el-descriptions :column="2" border :label-style="{width:'200px'}">
                    <el-descriptions-item >
                        <template slot="label">
                            车牌颜色（字典：1白色2黑色）
                        </template>
                        <span>{{ form.plateColor }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            车牌号
                        </template>
                        <span>{{ form.carNo }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            车型
                        </template>
                        <span>{{ form.carType }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            车种
                        </template>
                        <span>{{ form.carVehicle }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            轴数
                        </template>
                        <span>{{ form.carNum }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            通行标识（1人工2ETC）
                        </template>
                        <span>{{ form.passType }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            入口站id
                        </template>
                        <span>{{ form.inStationId }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            入口站
                        </template>
                        <span>{{ form.inStation }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            通行时间
                        </template>
                        <span>{{ form.inTime }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            出口站id
                        </template>
                        <span>{{ form.outStationId }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            出口站
                        </template>
                        <span>{{ form.outStation }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            出口时间
                        </template>
                        <span>{{ form.outTime }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            门架id
                        </template>
                        <span>{{ form.gantryStationId }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            门架名称
                        </template>
                        <span>{{ form.gantrytStation }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            经过时间
                        </template>
                        <span>{{ form.gantryTime }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            图片(附件ids)
                        </template>
                        <span>{{ form.fileIds }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            终止门架id
                        </template>
                        <span>{{ form.outGantryStationId }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            终止门架名称
                        </template>
                        <span>{{ form.outGantrytStation }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            终止经过时间
                        </template>
                        <span>{{ form.outGantryTime }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            终止图片(附件ids)
                        </template>
                        <span>{{ form.outFileIds }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）
                        </template>
                        <span>{{ form.escapedType }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            逃费类型名称
                        </template>
                        <span>{{ form.escapedTypeName }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            异常通行门架次数
                        </template>
                        <span>{{ form.escapedNum }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            是否为可疑车辆
                        </template>
                        <span>{{ form.isExcept }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            可疑原因
                        </template>
                        <span>{{ form.exceptRemark }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            可疑材料
                        </template>
                        <span>{{ form.exceptFileIds }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            核实状态（0未核实1已核实）
                        </template>
                        <span>{{ form.checkStatus }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            管理中心id
                        </template>
                        <span>{{ form.orgId }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            管理中心名称
                        </template>
                        <span>{{ form.orgName }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            是否在白名单（0否1是）
                        </template>
                        <span>{{ form.isWhite }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            白名单原因
                        </template>
                        <span>{{ form.whiteRemark }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            白名单材料
                        </template>
                        <span>{{ form.whiteFileIds }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            所属路线编码
                        </template>
                        <span>{{ form.roadCode }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            所属路线名称
                        </template>
                        <span>{{ form.roadName }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            所属路段编码
                        </template>
                        <span>{{ form.sectionCode }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            所属路段名称
                        </template>
                        <span>{{ form.sectionName }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            行驶轨迹id
                        </template>
                        <span>{{ form.trackId }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            行驶轨迹josn
                        </template>
                        <span>{{ form.trackJosn }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            轨迹点集合
                        </template>
                        <span>{{ form.trackNames }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            备用字段1
                        </template>
                        <span>{{ form.backCol1 }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            备用字段2
                        </template>
                        <span>{{ form.backCol2 }}</span>
                    </el-descriptions-item>
                    <el-descriptions-item >
                        <template slot="label">
                            备注
                        </template>
                        <span>{{ form.remark }}</span>
                    </el-descriptions-item>
                </el-descriptions>
            </template>
        </el-form>

    </div>
</template>

<script>
    import { getCarsuspiciousback, addCarsuspiciousback, updateCarsuspiciousback } from "@/api/manager/carsuspiciousback";
    import { dialogLoading } from '@/mixins/dialogLoading.js'

    export default {
        mixins: [dialogLoading],
        components: {
        },
        created() {
        },
        mounted() {
        },
        data() {
            return {
                flag: '',
                                carTypeList:[],
                                passTypeList:[],
                                escapedTypeList:[],
                datFromDisabled: false,
                form: {
                                id: null,
                                plateColor: null,
                                carNo: null,
                                carType: null,
                                carVehicle: null,
                                carNum: null,
                                passType: null,
                                inStationId: null,
                                inStation: null,
                                inTime: null,
                                outStationId: null,
                                outStation: null,
                                outTime: null,
                                gantryStationId: null,
                                gantrytStation: null,
                                gantryTime: null,
                                fileIds: null,
                                outGantryStationId: null,
                                outGantrytStation: null,
                                outGantryTime: null,
                                outFileIds: null,
                                escapedType: null,
                                escapedTypeName: null,
                                escapedNum: null,
                                isExcept: null,
                                exceptRemark: null,
                                exceptFileIds: null,
                                checkStatus: null,
                                orgId: null,
                                orgName: null,
                                isWhite: null,
                                whiteRemark: null,
                                whiteFileIds: null,
                                roadCode: null,
                                roadName: null,
                                sectionCode: null,
                                sectionName: null,
                                trackId: null,
                                trackJosn: null,
                                trackNames: null,
                                backCol1: null,
                                backCol2: null,
                                remark: null,
                                status: null,
                },
                // 表单校验
                rules: {
                                plateColor: [
                                { required: true, message: '车牌颜色（字典：1白色2黑色）不能为空', trigger: "blur" }
                            ],
                                carNo: [
                                { required: true, message: '车牌号不能为空', trigger: "blur" }
                            ],
                                carType: [
                                { required: true, message: '车型不能为空', trigger: "change" }
                            ],
                                carVehicle: [
                                { required: true, message: '车种不能为空', trigger: "blur" }
                            ],
                                carNum: [
                                { required: true, message: '轴数不能为空', trigger: "blur" }
                            ],
                                passType: [
                                { required: true, message: '通行标识（1人工2ETC）不能为空', trigger: "change" }
                            ],
                                inStationId: [
                                { required: true, message: '入口站id不能为空', trigger: "blur" }
                            ],
                                inStation: [
                                { required: true, message: '入口站不能为空', trigger: "blur" }
                            ],
                                inTime: [
                                { required: true, message: '通行时间不能为空', trigger: "blur" }
                            ],
                                outStationId: [
                                { required: true, message: '出口站id不能为空', trigger: "blur" }
                            ],
                                outStation: [
                                { required: true, message: '出口站不能为空', trigger: "blur" }
                            ],
                                outTime: [
                                { required: true, message: '出口时间不能为空', trigger: "blur" }
                            ],
                                gantryStationId: [
                                { required: true, message: '门架id不能为空', trigger: "blur" }
                            ],
                                gantrytStation: [
                                { required: true, message: '门架名称不能为空', trigger: "blur" }
                            ],
                                gantryTime: [
                                { required: true, message: '经过时间不能为空', trigger: "blur" }
                            ],
                                fileIds: [
                                { required: true, message: '图片(附件ids)不能为空', trigger: "blur" }
                            ],
                                outGantryStationId: [
                                { required: true, message: '终止门架id不能为空', trigger: "blur" }
                            ],
                                outGantrytStation: [
                                { required: true, message: '终止门架名称不能为空', trigger: "blur" }
                            ],
                                outGantryTime: [
                                { required: true, message: '终止经过时间不能为空', trigger: "blur" }
                            ],
                                outFileIds: [
                                { required: true, message: '终止图片(附件ids)不能为空', trigger: "blur" }
                            ],
                                escapedType: [
                                { required: true, message: '逃费类型（字典：1少轴2屏蔽3货车客标4有入无出5绿通换挂）不能为空', trigger: "change" }
                            ],
                                escapedTypeName: [
                                { required: true, message: '逃费类型名称不能为空', trigger: "blur" }
                            ],
                                escapedNum: [
                                { required: true, message: '异常通行门架次数不能为空', trigger: "blur" }
                            ],
                                isExcept: [
                                { required: true, message: '是否为可疑车辆不能为空', trigger: "blur" }
                            ],
                                exceptRemark: [
                                { required: true, message: '可疑原因不能为空', trigger: "blur" }
                            ],
                                exceptFileIds: [
                                { required: true, message: '可疑材料不能为空', trigger: "blur" }
                            ],
                                checkStatus: [
                                { required: true, message: '核实状态（0未核实1已核实）不能为空', trigger: "blur" }
                            ],
                                orgId: [
                                { required: true, message: '管理中心id不能为空', trigger: "blur" }
                            ],
                                orgName: [
                                { required: true, message: '管理中心名称不能为空', trigger: "blur" }
                            ],
                                isWhite: [
                                { required: true, message: '是否在白名单（0否1是）不能为空', trigger: "blur" }
                            ],
                                whiteRemark: [
                                { required: true, message: '白名单原因不能为空', trigger: "blur" }
                            ],
                                whiteFileIds: [
                                { required: true, message: '白名单材料不能为空', trigger: "blur" }
                            ],
                                roadCode: [
                                { required: true, message: '所属路线编码不能为空', trigger: "blur" }
                            ],
                                roadName: [
                                { required: true, message: '所属路线名称不能为空', trigger: "blur" }
                            ],
                                sectionCode: [
                                { required: true, message: '所属路段编码不能为空', trigger: "blur" }
                            ],
                                sectionName: [
                                { required: true, message: '所属路段名称不能为空', trigger: "blur" }
                            ],
                                trackId: [
                                { required: true, message: '行驶轨迹id不能为空', trigger: "blur" }
                            ],
                                trackJosn: [
                                { required: true, message: '行驶轨迹josn不能为空', trigger: "blur" }
                            ],
                                trackNames: [
                                { required: true, message: '轨迹点集合不能为空', trigger: "blur" }
                            ],
                                backCol1: [
                                { required: true, message: '备用字段1不能为空', trigger: "blur" }
                            ],
                                backCol2: [
                                { required: true, message: '备用字段2不能为空', trigger: "blur" }
                            ],
                                remark: [
                                { required: true, message: '备注不能为空', trigger: "blur" }
                            ],
                                status: [
                                { required: true, message: '状态（0正常1停用）不能为空', trigger: "blur" }
                            ],
                                tenantId: [
                                { required: true, message: '租户单位ID不能为空', trigger: "blur" }
                            ],
                },
            }
        },
        methods: {
            init({flag, id}) {
                this.flag = flag
                let o = {
                    'add': () => {
                        this.datFromDisabled = false
                    },
                    'edit': () => {
                        this.datFromDisabled = false
                        this.getData(id)
                    },
                    'view': () => {
                        this.datFromDisabled = true
                        this.getData(id)
                    }
                }
                o[flag]()
            },
            /** 提交按钮 */
            submitFormValidate() {
                this['$refs'].form.validate((valid) => {
                    if (valid) {
                        if (!this.openDialogLoading('form')) {
                            return false
                        }
                        this.submitForm()
                    }
                });
            },
            // 提交方法 此时提交的参数应都处理完毕
            submitForm() {
                if (this.form.id) {
                    updateCarsuspiciousback(this.form).then(response => {
                        this.msgSuccess("修改成功");
                        this.$emit('resSuccess')
                    }).catch(err => {
                        this.closeDialogLoading()
                    });
                } else {
                    addCarsuspiciousback(this.form).then(response => {
                        this.msgSuccess("新增成功");
                        this.$emit('resSuccess')
                    }).catch(err => {
                        this.closeDialogLoading()
                    });
                }
            },
            // 修改时回显数据
            getData(id) {
                getCarsuspiciousback(id).then(response => {
                    this.form = response.data;
                })
            }
        },
    }
</script>

<style lang='scss'>
</style>
