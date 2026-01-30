package com.ruoyi.web.util;

import org.apache.poi.hssf.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFCell;
import org.apache.poi.xssf.usermodel.XSSFRow;
import org.apache.poi.xssf.usermodel.XSSFSheet;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

import java.io.InputStream;
import java.text.DecimalFormat;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.List;
import java.util.regex.Pattern;


/**
 * 内容摘要: poi解析excel
 * 完成日期：2020-12-17
 * 编码作者：
 */
public class ImportSysUtil
{

    /**
     * 获取第几个sheet页面
     * @param index
     * @return
     * @throws Exception
     */
    public HSSFSheet getHSSFSheet03(InputStream is,int index) throws Exception
    {
        HSSFWorkbook workbook = new HSSFWorkbook(is);
        // 读取工作薄
        HSSFSheet sheet = workbook.getSheetAt(index);
        return sheet;
    }

    
    /**
     * 验证模板
     */
    public boolean colVdaExcel03(HSSFSheet sheet,String[] colsName) throws Exception
    {
        HSSFRow row = sheet.getRow(0);
        if (row == null)
        {
            return false;
        }
        else
        {
            // 获取每个单元格的内容
            for (int j = 0; j < colsName.length; j++)
            {
                // 获取指定单元格的内容
                String cellContent = getCellFormatValue03(row.getCell((short) j));
                if (!colsName[j].equals(cellContent))
                {
                    return false;
                }
            }

        }
        return true;
    }

    /**
     * 返回结果集
     */
    public List<String[]> dataRtnExcel03(HSSFSheet sheet,String[] colsName) throws Exception
    {
        List<String[]> list = new ArrayList<String[]>();
        int rowCount = sheet.getLastRowNum(); // 得到行数
        for (int i = 1; i <= rowCount; i++)
        {  
            String[] strs = new String[colsName.length];
            
            HSSFRow row = sheet.getRow(i);
            // 判断后面为空
            int cellCount;
            try
            {
                cellCount = row.getLastCellNum();
            }
            catch (NullPointerException e)
            {
                // 如果文件中没有到达最后一行，中间有空行则会报空指针，则让程序继续读下一行
                break;
            }
            // 如果行中遇到break则跳出循环
            if ("break".equals(getCellFormatValue03(row.getCell(0))) || "结束".equals(getCellFormatValue03(row.getCell(0))))
            {
                break;
            }

            // 循环列名
            for (int z = 0; z < colsName.length; z++)
            {
                strs[z] = isNull(getCellFormatValue03(row.getCell(z)));
            }
            list.add(strs);
        }
        
        return list;
    }

    /**
     * 根据HSSFCell类型设置数据 03
     * 
     * @param cell
     * @return
     */
    private String getCellFormatValue03(HSSFCell cell)
    {
        String cellvalue = "";
        if (cell != null)
        {
            // 判断当前Cell的Type
            switch (cell.getCellType())
            {
                // 如果当前Cell的Type为NUMERIC 判断单元格的值是否为数字类型
                case NUMERIC:
                    // 判断当前的cell是否为Date
                    if (HSSFDateUtil.isCellDateFormatted(cell))
                    {
                        // 如果是Date类型则，转化为Data格式
                        // 方法1：这样子的data格式是带时分秒的：2011-10-12 0:00:00
                        // cellvalue = cell.getDateCellValue().toLocaleString();
                        // 方法2：这样子的data格式是不带带时分秒的：2011-10-12
                        Date date = cell.getDateCellValue();
                        SimpleDateFormat sdf = new SimpleDateFormat("yyyy/MM/dd");
                        cellvalue = sdf.format(date);

                    }
                    else
                    {
                        DecimalFormat df = new DecimalFormat("#.##");
                        cellvalue = df.format(cell.getNumericCellValue());
                    }
                    break;
                // 公式
                case FORMULA:
                  /*  cellvalue = "FORMULA ";
                    break;*/
                    try {
                        cellvalue = String.valueOf(cell.getStringCellValue());
                    } catch (IllegalStateException e) {
                        cellvalue = String.valueOf(cell.getNumericCellValue());
                    }
                    break;
                // 如果当前Cell的Type为STRIN 判断单元格的值是否为字符串类型
                case STRING:
                    // 取得当前的Cell字符串
                    cellvalue = cell.getRichStringCellValue().getString();
                    break;
                // 判断单元格的值是否为布尔类型
                case BOOLEAN:
                    cellvalue = String.valueOf(cell.getBooleanCellValue());
                    break;
                // 空值
                case BLANK:
                    cellvalue = "";
                    break;
                case ERROR: // 故障
                    System.out.println(" 读取文件存在故障");
                    break;
                // 默认的Cell值
                default:
                    cellvalue = "";
            }
        }
        else
        {
            cellvalue = "";
        }
        return cellvalue.trim();
    }

   
    /**
     * 取报错信息BO
     * 
     * @param row 行数
     * @param colName 列名
     * @param message 错误信息
     * @return ImportErrorBO 信息
     */
    public ImportErrorEntity getErrorBO(int row, String colName, String message)
    {
		ImportErrorEntity errorBO = new ImportErrorEntity();
        errorBO.setRowNo(row+1);
        errorBO.setColName(colName);
        errorBO.setMessage(message);
        return errorBO;
    }

    /**
     * 正则验证,符合为true
     * 
     * @param value
     *            行数
     * @param regex
     *            正则表达式
     * @return boolean 信息
     */
    public boolean validateValueRegex(String value, String regex)
    {
        boolean enable = false;
        enable = Pattern.matches(regex, value);
        
        return enable;
    }
    

    /**
     * 判断是否为空
     * 
     * @param names
     * @return
     */
    private String isNull(Object names)
    {
        if (names == null)
        {
            return "";
        }
        else
        {
            return names.toString();
        }
    }
    

    
    /**
     * 获取第几个sheet页面
     * @param is
     * @param index
     * @return
     * @throws Exception
     */
    public XSSFSheet getXSSFSheet(InputStream is,int index) throws Exception
    {
        XSSFWorkbook workbook = new XSSFWorkbook(is);
        // 读取工作薄
        XSSFSheet sheet = workbook.getSheetAt(index);
        return sheet;
    }


	/**
	 * 验证模板
	 */
	public boolean colVdaExcel07(XSSFSheet sheet,String[] colsName) throws Exception
	{
		XSSFRow row = sheet.getRow(0);
		if (row == null)
		{
			return false;
		}
		else
		{
			// 获取每个单元格的内容
			for (int j = 0; j < colsName.length; j++)
			{
				// 获取指定单元格的内容
				String cellContent = getCellFormatValue07(row.getCell(j));

				if (!colsName[j].equals(cellContent))
				{
					return false;
				}
			}

		}
		return true;
	}
    
    public boolean colVdaExcel08(XSSFSheet sheet,String[] colsName,Integer num) throws Exception
    {
        XSSFRow row = sheet.getRow(num);
        if (row == null)
        {
            return false;
        }
        else
        {
            // 获取每个单元格的内容
            for (int j = 0; j < colsName.length; j++)
            {
                // 获取指定单元格的内容
                String cellContent = getCellFormatValue07(row.getCell(j));
                
                if (!colsName[j].equals(cellContent))
                {
                    return false;
                }
            }
            
        }
        return true;
    }

    /**
     * 验证模板 2022.1.6新类型模板校验 增加表头信息 由第四行开始
     */
    public boolean colVdaExcel07Row3(XSSFSheet sheet,String[] colsName) throws Exception
    {
        XSSFRow row = sheet.getRow(3);
        if (row == null)
        {
            return false;
        }
        else
        {
            // 获取每个单元格的内容
            for (int j = 0; j < colsName.length; j++)
            {
                // 获取指定单元格的内容
                String cellContent = getCellFormatValue07(row.getCell(j));

                if (!colsName[j].equals(cellContent))
                {
                    return false;
                }
            }

        }
        return true;
    }



    
    public List<String[]> dataRtnExcel07(XSSFSheet sheet,String[] colsName) throws Exception
    {
        List<String[]> list = new ArrayList<String[]>();
        int rowCount = sheet.getLastRowNum(); // 得到行数
        for (int i = 1; i <= rowCount; i++)
        {
            String[] strs = new String[colsName.length];

            XSSFRow row = sheet.getRow(i);
            // 判断后面为空
            int cellCount;
            try
            {
                cellCount = row.getLastCellNum();
            }
            catch (NullPointerException e)
            {
                // 如果文件中没有到达最后一行，中间有空行则会报空指针，则让程序继续读下一行
                break;
            }
            // 如果行中遇到break则跳出循环
            if ("break".equals(getCellFormatValue07(row.getCell(0))) || "结束".equals(getCellFormatValue07(row.getCell(0))))
            {
                break;
            }

            // 循环列名
            for (int z = 0; z < colsName.length; z++)
            {
                strs[z] = isNull(getCellFormatValue07(row.getCell(z)));
            }
            list.add(strs);
        }

        return list;
    }
    
    /**
     * 多列数据表头验证
     * @param sheet
     * @param colsName
     * @return
     * @throws Exception
     */
    public List<String[]> dataRtnExcel08(XSSFSheet sheet,String[] colsName,Integer[] rowNume,Integer num) throws Exception
    {
        List<String[]> list = new ArrayList<String[]>();
        int rowCount = sheet.getLastRowNum(); // 得到行数
        for (int i = num; i <= rowCount; i++)
        {
            String[] strs = new String[colsName.length];
            
            XSSFRow row = sheet.getRow(i);
            // 判断后面为空
            int cellCount;
            try
            {
                cellCount = row.getLastCellNum();
            }
            catch (NullPointerException e)
            {
                // 如果文件中没有到达最后一行，中间有空行则会报空指针，则让程序继续读下一行
                break;
            }
            // 如果行中遇到break则跳出循环
            if ("break".equals(getCellFormatValue07(row.getCell(0))) || "结束".equals(getCellFormatValue07(row.getCell(0))))
            {
                break;
            }
            
            // 循环列名
            for (int z = 0; z < colsName.length; z++)
            {
                if ( !Arrays.asList(rowNume).contains(z)){
                    strs[z] = isNull(getCellFormatValue08(row.getCell(z)));
                }
            }
            list.add(strs);
        }
        
        return list;
    }

    /**
     * 验证模板 2022.1.6新类型模板校验 增加表头信息 由第四行开始 并增加公式
     */
    public List<String[]> dataRtnExcel07Row3(XSSFSheet sheet,String[] colsName) throws Exception
    {
        List<String[]> list = new ArrayList<String[]>();
        int rowCount = sheet.getLastRowNum()-1; // 得到行数
        for (int i = 4; i <= rowCount; i++) {
            String[] strs = new String[colsName.length];

            XSSFRow row = sheet.getRow(i);
            // 判断后面为空
            int cellCount;
            try
            {
                cellCount = row.getLastCellNum();
            }
            catch (NullPointerException e)
            {
                // 如果文件中没有到达最后一行，中间有空行则会报空指针，则让程序继续读下一行
                break;
            }
            // 如果行中遇到break则跳出循环
            if ("break".equals(getCellFormatValue07(row.getCell(0))) || "结束".equals(getCellFormatValue07(row.getCell(0))))
            {
                break;
            }

            // 循环列名
            for (int z = 0; z < colsName.length; z++)
            {
                strs[z] = isNull(getCellFormatValue07(row.getCell(z)));
            }
            list.add(strs);
        }

        return list;
    }

    private String getCellFormatValue07(XSSFCell cell)
    {
        String cellvalue = "";
        if (cell != null)
        {
            // 判断当前Cell的Type
            switch (cell.getCellType())
            {
                // 如果当前Cell的Type为NUMERIC 判断单元格的值是否为数字类型
                case NUMERIC:
                    // 判断当前的cell是否为Date
                    if (HSSFDateUtil.isCellDateFormatted(cell))
                    {
                        // 如果是Date类型则，转化为Data格式
                        // 方法1：这样子的data格式是带时分秒的：2011-10-12 0:00:00
                        // cellvalue = cell.getDateCellValue().toLocaleString();
                        // 方法2：这样子的data格式是不带带时分秒的：2011-10-12
                        Date date = cell.getDateCellValue();
                        SimpleDateFormat sdf = new SimpleDateFormat("yyyy/MM/dd");
                        cellvalue = sdf.format(date);

                    }
                    else
                    {
                        DecimalFormat df = new DecimalFormat("#.##");
                        cellvalue = df.format(cell.getNumericCellValue());
                    }
                    break;
                // 公式 公式只有在每行的单项总价里有，这里需要获取
                case FORMULA:
//                    cellvalue = "FORMULA ";
                    DecimalFormat df = new DecimalFormat("#.##");
                    cellvalue = df.format(cell.getNumericCellValue());
                    break;
                // 如果当前Cell的Type为STRIN 判断单元格的值是否为字符串类型
                case STRING:
                    // 取得当前的Cell字符串
                    cellvalue = cell.getRichStringCellValue().getString();
                    break;
                // 判断单元格的值是否为布尔类型
                case BOOLEAN:
                    cellvalue = String.valueOf(cell.getBooleanCellValue());
                    break;
                // 空值
                case BLANK:
                    cellvalue = "";
                    break;
                case ERROR: // 故障
                    System.out.println(" 读取文件存在故障");
                    break;
                // 默认的Cell值
                default:
                    cellvalue = "";
            }
        }
        else
        {
            cellvalue = "";
        }
        return cellvalue.trim();
    }
    
    /**
     * 获取单元格值,日期为yyyy-MM-dd hh:mm:ss
     * @param cell
     * @return
     */
    private String getCellFormatValue08(XSSFCell cell)
    {
        String cellvalue = "";
        if (cell != null)
        {
            // 判断当前Cell的Type
            switch (cell.getCellType())
            {
                // 如果当前Cell的Type为NUMERIC 判断单元格的值是否为数字类型
                case NUMERIC:
                    // 判断当前的cell是否为Date
                    if (HSSFDateUtil.isCellDateFormatted(cell))
                    {
                        // 如果是Date类型则，转化为Data格式
                        // 方法1：这样子的data格式是带时分秒的：2011-10-12 0:00:00
                        // cellvalue = cell.getDateCellValue().toLocaleString();
                        // 方法2：这样子的data格式是不带带时分秒的：2011-10-12
                        Date date = cell.getDateCellValue();
                        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
                        cellvalue = sdf.format(date);
                        
                    }
                    else
                    {
                        DecimalFormat df = new DecimalFormat("#.##");
                        cellvalue = df.format(cell.getNumericCellValue());
                    }
                    break;
                // 公式 公式只有在每行的单项总价里有，这里需要获取
                case FORMULA:
//                    cellvalue = "FORMULA ";
                    DecimalFormat df = new DecimalFormat("#.##");
                    cellvalue = df.format(cell.getNumericCellValue());
                    break;
                // 如果当前Cell的Type为STRIN 判断单元格的值是否为字符串类型
                case STRING:
                    // 取得当前的Cell字符串
                    cellvalue = cell.getRichStringCellValue().getString();
                    break;
                // 判断单元格的值是否为布尔类型
                case BOOLEAN:
                    cellvalue = String.valueOf(cell.getBooleanCellValue());
                    break;
                // 空值
                case BLANK:
                    cellvalue = "";
                    break;
                case ERROR: // 故障
                    System.out.println(" 读取文件存在故障");
                    break;
                // 默认的Cell值
                default:
                    cellvalue = "";
            }
        }
        else
        {
            cellvalue = "";
        }
        return cellvalue.trim();
    }
}
