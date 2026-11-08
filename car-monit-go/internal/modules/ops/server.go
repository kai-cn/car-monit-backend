// JAVA 对照: ruoyi-admin/src/main/java/com/ruoyi/web/controller/monitor/ServerController.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/web/domain/Server.java
// JAVA 对照: ruoyi-framework/src/main/java/com/ruoyi/framework/web/domain/server/{Cpu,Mem,Jvm,Sys,SysFileInfo}.java
// 类/职责: 服务器监控 — CPU / 内存 / 运行时（JVM 面板）/ 主机 / 磁盘
// 对应 Go 文件: internal/modules/ops/server.go
//
// DIFF: Java 用 OSHI 采集，Go 用 gopsutil（Python 版用 psutil，三者语义最接近）。
// CPU 占用率同样靠两次采样求差，本端点**固定阻塞 1 秒**（OSHI_WAIT_SECOND = 1000）。
// DIFF: gopsutil 的 CPU times 单位是秒，乘以 100 换算成 OSHI 的 tick 量级 —— 与 Python 版
// 的处理一致，保证 Cpu.total 的量级可比（百分比字段是比值，与单位无关）。
// DIFF: Go 没有 JVM，Jvm 面板改用宿主机内存 + Go 运行时信息（与 Python 版选择一致）：
// total/max 取物理内存、free 取可用内存，因此 used/usage 是整机内存占用，不会出现假值。
// DIFF: 磁盘采集失败的分区**跳过**（Java 的 OSHI 会抛 IOException 导致整页 500）；
// 与 Python 版一致：少一块盘优于整页监控不可用（Java 的 OSHI 会抛 IOException 导致 500）。
// DIFF: Windows 上 gopsutil 不提供卷标，typeName 退回到设备名（Python 版取到了卷标）。
// DIFF: Jackson 对 double 总是输出 ".0" 后缀，Go 默认会省略；这里用 javaFloat 补齐。
package ops

import (
	"fmt"
	"go/build"
	"math"
	"net"
	"os"
	"runtime"
	"strconv"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/shirou/gopsutil/v4/cpu"
	"github.com/shirou/gopsutil/v4/disk"
	"github.com/shirou/gopsutil/v4/host"
	"github.com/shirou/gopsutil/v4/mem"

	"car-monit-go/internal/app"
	"car-monit-go/internal/middleware"
	"car-monit-go/internal/web"
)

// JAVA 对照: Server.OSHI_WAIT_SECOND —— CPU 使用率必须两次采样，响应时间下限 1 秒。
const oshiWaitSecond = 1000

// OSHI 在 Linux 上以 HZ=100 计数；gopsutil 给秒，乘 100 保持 Cpu.total 量级。
const ticksPerSecond = 100.0

// processStartTime 等价 DateUtils.getServerStartDate()：Go 无 JVM，取进程（包）启动时间。
var processStartTime = time.Now()

// javaFloat 复刻 Jackson 对 double 的输出：整数值也带 ".0"。
type javaFloat float64

func (v javaFloat) MarshalJSON() ([]byte, error) {
	s := strconv.FormatFloat(float64(v), 'f', -1, 64)
	if !strings.Contains(s, ".") {
		s += ".0"
	}
	return []byte(s), nil
}

// javaRound 对应 Arith.round(v, scale)：BigDecimal HALF_UP（与 math.Round 同为远离零）。
func javaRound(v float64, scale int) float64 {
	p := math.Pow(10, float64(scale))
	return math.Round(v*p) / p
}

// javaDiv 对应 Arith.div(v1, v2, scale)。Java 在除数为 0 时抛 ArithmeticException（500），
// 这里退化返回 0；实践上 1 秒采样后的 CPU tick 总和不可能为 0。
func javaDiv(v1, v2 float64, scale int) float64 {
	if v2 == 0 {
		return 0
	}
	return javaRound(v1/v2, scale)
}

type serverCPU struct {
	CpuNum int       `json:"cpuNum"`
	Total  javaFloat `json:"total"`
	Sys    javaFloat `json:"sys"`
	Used   javaFloat `json:"used"`
	Wait   javaFloat `json:"wait"`
	Free   javaFloat `json:"free"`
}

type serverMem struct {
	Total javaFloat `json:"total"`
	Used  javaFloat `json:"used"`
	Free  javaFloat `json:"free"`
	Usage javaFloat `json:"usage"`
}

type serverJvm struct {
	Total     javaFloat `json:"total"`
	Max       javaFloat `json:"max"`
	Free      javaFloat `json:"free"`
	Used      javaFloat `json:"used"`
	Usage     javaFloat `json:"usage"`
	Name      string    `json:"name"`
	Version   string    `json:"version"`
	Home      string    `json:"home"`
	StartTime string    `json:"startTime"`
	RunTime   string    `json:"runTime"`
	InputArgs string    `json:"inputArgs"`
}

type serverSys struct {
	ComputerName string `json:"computerName"`
	ComputerIP   string `json:"computerIp"`
	UserDir      string `json:"userDir"`
	OSName       string `json:"osName"`
	OSArch       string `json:"osArch"`
}

type serverSysFile struct {
	DirName     string    `json:"dirName"`
	SysTypeName string    `json:"sysTypeName"`
	TypeName    string    `json:"typeName"`
	Total       string    `json:"total"`
	Free        string    `json:"free"`
	Used        string    `json:"used"`
	Usage       javaFloat `json:"usage"`
}

// serverInfo 对应 Server 对象本身（Jackson 的字段顺序 cpu -> mem -> jvm -> sys -> sysFiles）。
type serverInfo struct {
	CPU      *serverCPU      `json:"cpu"`
	Mem      *serverMem      `json:"mem"`
	Jvm      *serverJvm      `json:"jvm"`
	Sys      *serverSys      `json:"sys"`
	SysFiles []serverSysFile `json:"sysFiles"`
}

type serverHandler struct {
	app *app.App
}

// GetInfo 对应 GET /monitor/server（`monitor:server:list`）。阻塞约 1 秒。
func (h *serverHandler) GetInfo(c *gin.Context) {
	info, err := collectServerInfo(h.app)
	if err != nil {
		web.JSON(c, web.ErrorResult(err))
		return
	}
	web.JSON(c, web.SuccessData(info))
}

// collectServerInfo 对应 Server.copyTo()：cpu -> mem -> sys -> jvm -> sysFiles。
func collectServerInfo(a *app.App) (*serverInfo, error) {
	cpuInfo, err := collectCPU()
	if err != nil {
		return nil, err
	}
	memory, err := mem.VirtualMemory()
	if err != nil {
		return nil, err
	}
	hostInfo, err := host.Info()
	if err != nil {
		return nil, err
	}

	return &serverInfo{
		CPU:      cpuInfo,
		Mem:      collectMem(memory),
		Jvm:      collectJvm(memory),
		Sys:      collectSys(hostInfo),
		SysFiles: collectSysFiles(a),
	}, nil
}

// collectCPU 对应 Server.setCpuInfo：两次 getSystemCpuLoadTicks 求差。
func collectCPU() (*serverCPU, error) {
	prev, err := cpu.Times(false)
	if err != nil {
		return nil, err
	}
	if oshiWaitSecond > 0 {
		time.Sleep(time.Duration(oshiWaitSecond) * time.Millisecond)
	}
	cur, err := cpu.Times(false)
	if err != nil {
		return nil, err
	}
	if len(prev) == 0 || len(cur) == 0 {
		return nil, fmt.Errorf("读取 CPU 信息失败")
	}

	// TickType 顺序：NICE, IRQ, SOFTIRQ, STEAL, SYSTEM, USER, IOWAIT, IDLE。
	nice := (cur[0].Nice - prev[0].Nice) * ticksPerSecond
	irq := (cur[0].Irq - prev[0].Irq) * ticksPerSecond
	softirq := (cur[0].Softirq - prev[0].Softirq) * ticksPerSecond
	steal := (cur[0].Steal - prev[0].Steal) * ticksPerSecond
	sys := (cur[0].System - prev[0].System) * ticksPerSecond
	user := (cur[0].User - prev[0].User) * ticksPerSecond
	iowait := (cur[0].Iowait - prev[0].Iowait) * ticksPerSecond
	idle := (cur[0].Idle - prev[0].Idle) * ticksPerSecond
	total := user + nice + sys + idle + iowait + irq + softirq + steal

	pct := func(ticks float64) javaFloat {
		if total == 0 {
			return 0
		}
		return javaFloat(javaRound(ticks/total*100, 2))
	}
	return &serverCPU{
		CpuNum: runtime.NumCPU(),
		// JAVA 对照: Cpu.getTotal —— 只乘 100、不除以 total（上游既有怪癖，照抄）。
		Total: javaFloat(javaRound(total*100, 2)),
		Sys:   pct(sys),
		Used:  pct(user),
		Wait:  pct(iowait),
		Free:  pct(idle),
	}, nil
}

// collectMem 对应 Server.setMemInfo：used = total - available，free = available。
func collectMem(memory *mem.VirtualMemoryStat) *serverMem {
	const gb = 1024 * 1024 * 1024
	used := memory.Total - memory.Available
	return &serverMem{
		Total: javaFloat(javaDiv(float64(memory.Total), gb, 2)),
		Used:  javaFloat(javaDiv(float64(used), gb, 2)),
		Free:  javaFloat(javaDiv(float64(memory.Available), gb, 2)),
		Usage: javaFloat(javaRound(javaDiv(float64(used), float64(memory.Total), 4)*100, 2)),
	}
}

// collectJvm 对应 Server.setJvmInfo + Jvm 的各 getter。Go 无 JVM，面板取宿主机内存
// （见文件头 DIFF），版本 / home / name 取 Go 运行时信息。
func collectJvm(memory *mem.VirtualMemoryStat) *serverJvm {
	const mb = 1024 * 1024
	total := float64(memory.Total)
	free := float64(memory.Available)
	used := total - free
	return &serverJvm{
		Total:     javaFloat(javaDiv(total, mb, 2)),
		Max:       javaFloat(javaDiv(total, mb, 2)),
		Free:      javaFloat(javaDiv(free, mb, 2)),
		Used:      javaFloat(javaDiv(used, mb, 2)),
		Usage:     javaFloat(javaRound(javaDiv(used, total, 4)*100, 2)),
		Name:      "Go " + runtime.Version() + " " + runtime.GOOS + "/" + runtime.GOARCH,
		Version:   runtime.Version(),
		Home:      build.Default.GOROOT,
		StartTime: processStartTime.Format("2006-01-02 15:04:05"),
		RunTime:   javaTimeDistance(time.Now(), processStartTime),
		InputArgs: "[" + strings.Join(os.Args, ", ") + "]",
	}
}

// javaTimeDistance 对应 DateUtils.timeDistance：x天x小时x分钟。
func javaTimeDistance(end, start time.Time) string {
	const (
		day  = int64(1000 * 24 * 60 * 60)
		hour = int64(1000 * 60 * 60)
		min  = int64(1000 * 60)
	)
	diff := end.UnixMilli() - start.UnixMilli()
	return fmt.Sprintf("%d天%d小时%d分钟", diff/day, diff%day/hour, diff%day%hour/min)
}

// collectSys 对应 Server.setSysInfo（System.getProperties 的 os.name / os.arch / user.dir）。
func collectSys(info *host.InfoStat) *serverSys {
	hostName, err := os.Hostname()
	if err != nil || hostName == "" {
		hostName = "未知"
	}
	userDir, _ := os.Getwd()
	return &serverSys{
		ComputerName: hostName,
		ComputerIP:   hostIPv4(),
		UserDir:      userDir,
		OSName:       javaOSName(info),
		OSArch:       javaOSArch(info),
	}
}

// hostIPv4 对应 IpUtils.getHostIp：本机主机名解析出的 IPv4，失败回 127.0.0.1。
func hostIPv4() string {
	hostName, err := os.Hostname()
	if err != nil {
		return "127.0.0.1"
	}
	addrs, err := net.LookupHost(hostName)
	if err != nil {
		return "127.0.0.1"
	}
	for _, addr := range addrs {
		if ip := net.ParseIP(addr); ip != nil && ip.To4() != nil {
			return addr
		}
	}
	if len(addrs) > 0 {
		return addrs[0]
	}
	return "127.0.0.1"
}

// javaOSName 近似 Java 的 System.getProperty("os.name")：
// Windows 按 build 号区分 10/11，Linux 为 "Linux"，macOS 为 "Mac OS X"。
func javaOSName(info *host.InfoStat) string {
	switch runtime.GOOS {
	case "windows":
		build := 0
		parts := strings.Split(info.PlatformVersion, ".")
		if len(parts) > 0 {
			build, _ = strconv.Atoi(parts[len(parts)-1])
		}
		if build >= 22000 {
			return "Windows 11"
		}
		return "Windows 10"
	case "darwin":
		return "Mac OS X"
	case "linux":
		return "Linux"
	default:
		if runtime.GOOS == "" {
			return runtime.GOOS
		}
		return strings.ToUpper(runtime.GOOS[:1]) + runtime.GOOS[1:]
	}
}

// javaOSArch 对应 os.arch（amd64 / aarch64 / x86）。
func javaOSArch(info *host.InfoStat) string {
	switch info.KernelArch {
	case "x86_64":
		return "amd64"
	case "arm64":
		return "aarch64"
	case "i686", "i386":
		return "x86"
	case "":
		return runtime.GOARCH
	default:
		return info.KernelArch
	}
}

// collectSysFiles 对应 Server.setSysFiles：逐分区采集容量，失败的分区跳过（见文件头 DIFF）。
func collectSysFiles(a *app.App) []serverSysFile {
	partitions, err := disk.Partitions(false)
	if err != nil {
		if a != nil && a.Log != nil {
			a.Log.Warn("读取磁盘分区失败", "err", err)
		}
		return []serverSysFile{}
	}
	rows := make([]serverSysFile, 0, len(partitions))
	for _, partition := range partitions {
		usage, err := disk.Usage(partition.Mountpoint)
		if err != nil {
			if a != nil && a.Log != nil {
				a.Log.Debug("磁盘采集跳过", "mount", partition.Mountpoint, "err", err)
			}
			continue
		}
		mount := partition.Mountpoint
		// JAVA 对照: OSHI OSFileStore#getMount，Windows 显示 "C:\" 而不是 "C:"。
		if runtime.GOOS == "windows" && len(mount) == 2 && mount[1] == ':' {
			mount += "\\"
		}
		used := usage.Total - usage.Free
		rows = append(rows, serverSysFile{
			DirName:     mount,
			SysTypeName: partition.Fstype,
			TypeName:    partition.Device,
			Total:       convertFileSize(usage.Total),
			Free:        convertFileSize(usage.Free),
			Used:        convertFileSize(used),
			Usage:       javaFloat(javaRound(javaDiv(float64(used), float64(usage.Total), 4)*100, 2)),
		})
	}
	return rows
}

// convertFileSize 对应 Server.convertFileSize：GB 恒 1 位小数，MB/KB 大于 100 时取整。
func convertFileSize(size uint64) string {
	const (
		kb = uint64(1024)
		mb = kb * 1024
		gb = mb * 1024
	)
	switch {
	case size >= gb:
		return fmt.Sprintf("%.1f GB", javaRound(float64(size)/float64(gb), 1))
	case size >= mb:
		value := float64(size) / float64(mb)
		if value > 100 {
			return fmt.Sprintf("%.0f MB", javaRound(value, 0))
		}
		return fmt.Sprintf("%.1f MB", javaRound(value, 1))
	case size >= kb:
		value := float64(size) / float64(kb)
		if value > 100 {
			return fmt.Sprintf("%.0f KB", javaRound(value, 0))
		}
		return fmt.Sprintf("%.1f KB", javaRound(value, 1))
	default:
		return fmt.Sprintf("%d B", size)
	}
}

// newServerRoutes 注册 /monitor/server。
func newServerRoutes(reg gin.IRouter, a *app.App) {
	h := &serverHandler{app: a}
	g := reg.Group("/monitor/server")
	g.GET("", middleware.Perm("monitor:server:list"), h.GetInfo)
}
