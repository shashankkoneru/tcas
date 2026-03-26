; ModuleID = 'tcas.c'
source_filename = "tcas.c"
target datalayout = "e-m:o-i64:64-i128:128-n32:64-S128-Fn32"
target triple = "arm64-apple-macosx26.0.0"

@Positive_RA_Alt_Thresh = common global [4 x i32] zeroinitializer, align 4
@Alt_Layer_Value = common global i32 0, align 4
@Climb_Inhibit = common global i32 0, align 4
@Up_Separation = common global i32 0, align 4
@Down_Separation = common global i32 0, align 4
@Cur_Vertical_Sep = common global i32 0, align 4
@Own_Tracked_Alt = common global i32 0, align 4
@Other_Tracked_Alt = common global i32 0, align 4
@High_Confidence = common global i32 0, align 4
@Own_Tracked_Alt_Rate = common global i32 0, align 4
@Other_Capability = common global i32 0, align 4
@Two_of_Three_Reports_Valid = common global i32 0, align 4
@Other_RAC = common global i32 0, align 4
@__stdoutp = external global ptr, align 8
@.str = private unnamed_addr constant [35 x i8] c"Error: Command line arguments are\0A\00", align 1
@.str.1 = private unnamed_addr constant [63 x i8] c"Cur_Vertical_Sep, High_Confidence, Two_of_Three_Reports_Valid\0A\00", align 1
@.str.2 = private unnamed_addr constant [58 x i8] c"Own_Tracked_Alt, Own_Tracked_Alt_Rate, Other_Tracked_Alt\0A\00", align 1
@.str.3 = private unnamed_addr constant [49 x i8] c"Alt_Layer_Value, Up_Separation, Down_Separation\0A\00", align 1
@.str.4 = private unnamed_addr constant [44 x i8] c"Other_RAC, Other_Capability, Climb_Inhibit\0A\00", align 1
@.str.5 = private unnamed_addr constant [4 x i8] c"%d\0A\00", align 1

; Function Attrs: noinline nounwind optnone ssp uwtable(sync)
define void @initialize() #0 {
  store i32 400, ptr @Positive_RA_Alt_Thresh, align 4
  store i32 500, ptr getelementptr inbounds ([4 x i32], ptr @Positive_RA_Alt_Thresh, i64 0, i64 1), align 4
  store i32 640, ptr getelementptr inbounds ([4 x i32], ptr @Positive_RA_Alt_Thresh, i64 0, i64 2), align 4
  store i32 740, ptr getelementptr inbounds ([4 x i32], ptr @Positive_RA_Alt_Thresh, i64 0, i64 3), align 4
  ret void
}

; Function Attrs: noinline nounwind optnone ssp uwtable(sync)
define i32 @ALIM() #0 {
  %1 = load i32, ptr @Alt_Layer_Value, align 4
  %2 = sext i32 %1 to i64
  %3 = getelementptr inbounds [4 x i32], ptr @Positive_RA_Alt_Thresh, i64 0, i64 %2
  %4 = load i32, ptr %3, align 4
  ret i32 %4
}

; Function Attrs: noinline nounwind optnone ssp uwtable(sync)
define i32 @Inhibit_Biased_Climb() #0 {
  %1 = load i32, ptr @Climb_Inhibit, align 4
  %2 = icmp ne i32 %1, 0
  br i1 %2, label %3, label %6

3:                                                ; preds = %0
  %4 = load i32, ptr @Up_Separation, align 4
  %5 = add nsw i32 %4, 100
  br label %8

6:                                                ; preds = %0
  %7 = load i32, ptr @Up_Separation, align 4
  br label %8

8:                                                ; preds = %6, %3
  %9 = phi i32 [ %5, %3 ], [ %7, %6 ]
  ret i32 %9
}

; Function Attrs: noinline nounwind optnone ssp uwtable(sync)
define i32 @Non_Crossing_Biased_Climb() #0 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  %3 = alloca i32, align 4
  %4 = call i32 @Inhibit_Biased_Climb()
  %5 = load i32, ptr @Down_Separation, align 4
  %6 = icmp sgt i32 %4, %5
  %7 = zext i1 %6 to i32
  store i32 %7, ptr %1, align 4
  %8 = load i32, ptr %1, align 4
  %9 = icmp ne i32 %8, 0
  br i1 %9, label %10, label %26

10:                                               ; preds = %0
  %11 = call i32 @Own_Below_Threat()
  %12 = icmp ne i32 %11, 0
  br i1 %12, label %13, label %23

13:                                               ; preds = %10
  %14 = call i32 @Own_Below_Threat()
  %15 = icmp ne i32 %14, 0
  br i1 %15, label %16, label %21

16:                                               ; preds = %13
  %17 = load i32, ptr @Down_Separation, align 4
  %18 = call i32 @ALIM()
  %19 = icmp sge i32 %17, %18
  %20 = xor i1 %19, true
  br label %21

21:                                               ; preds = %16, %13
  %22 = phi i1 [ false, %13 ], [ %20, %16 ]
  br label %23

23:                                               ; preds = %21, %10
  %24 = phi i1 [ true, %10 ], [ %22, %21 ]
  %25 = zext i1 %24 to i32
  store i32 %25, ptr %3, align 4
  br label %39

26:                                               ; preds = %0
  %27 = call i32 @Own_Above_Threat()
  %28 = icmp ne i32 %27, 0
  br i1 %28, label %29, label %36

29:                                               ; preds = %26
  %30 = load i32, ptr @Cur_Vertical_Sep, align 4
  %31 = icmp sge i32 %30, 300
  br i1 %31, label %32, label %36

32:                                               ; preds = %29
  %33 = load i32, ptr @Up_Separation, align 4
  %34 = call i32 @ALIM()
  %35 = icmp sge i32 %33, %34
  br label %36

36:                                               ; preds = %32, %29, %26
  %37 = phi i1 [ false, %29 ], [ false, %26 ], [ %35, %32 ]
  %38 = zext i1 %37 to i32
  store i32 %38, ptr %3, align 4
  br label %39

39:                                               ; preds = %36, %23
  %40 = load i32, ptr %3, align 4
  ret i32 %40
}

; Function Attrs: noinline nounwind optnone ssp uwtable(sync)
define i32 @Non_Crossing_Biased_Descend() #0 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  %3 = alloca i32, align 4
  %4 = call i32 @Inhibit_Biased_Climb()
  %5 = load i32, ptr @Down_Separation, align 4
  %6 = icmp sgt i32 %4, %5
  %7 = zext i1 %6 to i32
  store i32 %7, ptr %1, align 4
  %8 = load i32, ptr %1, align 4
  %9 = icmp ne i32 %8, 0
  br i1 %9, label %10, label %23

10:                                               ; preds = %0
  %11 = call i32 @Own_Below_Threat()
  %12 = icmp ne i32 %11, 0
  br i1 %12, label %13, label %20

13:                                               ; preds = %10
  %14 = load i32, ptr @Cur_Vertical_Sep, align 4
  %15 = icmp sge i32 %14, 300
  br i1 %15, label %16, label %20

16:                                               ; preds = %13
  %17 = load i32, ptr @Down_Separation, align 4
  %18 = call i32 @ALIM()
  %19 = icmp sge i32 %17, %18
  br label %20

20:                                               ; preds = %16, %13, %10
  %21 = phi i1 [ false, %13 ], [ false, %10 ], [ %19, %16 ]
  %22 = zext i1 %21 to i32
  store i32 %22, ptr %3, align 4
  br label %38

23:                                               ; preds = %0
  %24 = call i32 @Own_Above_Threat()
  %25 = icmp ne i32 %24, 0
  br i1 %25, label %26, label %35

26:                                               ; preds = %23
  %27 = call i32 @Own_Above_Threat()
  %28 = icmp ne i32 %27, 0
  br i1 %28, label %29, label %33

29:                                               ; preds = %26
  %30 = load i32, ptr @Up_Separation, align 4
  %31 = call i32 @ALIM()
  %32 = icmp sge i32 %30, %31
  br label %33

33:                                               ; preds = %29, %26
  %34 = phi i1 [ false, %26 ], [ %32, %29 ]
  br label %35

35:                                               ; preds = %33, %23
  %36 = phi i1 [ true, %23 ], [ %34, %33 ]
  %37 = zext i1 %36 to i32
  store i32 %37, ptr %3, align 4
  br label %38

38:                                               ; preds = %35, %20
  %39 = load i32, ptr %3, align 4
  ret i32 %39
}

; Function Attrs: noinline nounwind optnone ssp uwtable(sync)
define i32 @Own_Below_Threat() #0 {
  %1 = load i32, ptr @Own_Tracked_Alt, align 4
  %2 = load i32, ptr @Other_Tracked_Alt, align 4
  %3 = icmp slt i32 %1, %2
  %4 = zext i1 %3 to i32
  ret i32 %4
}

; Function Attrs: noinline nounwind optnone ssp uwtable(sync)
define i32 @Own_Above_Threat() #0 {
  %1 = load i32, ptr @Other_Tracked_Alt, align 4
  %2 = load i32, ptr @Own_Tracked_Alt, align 4
  %3 = icmp slt i32 %1, %2
  %4 = zext i1 %3 to i32
  ret i32 %4
}

; Function Attrs: noinline nounwind optnone ssp uwtable(sync)
define i32 @alt_sep_test() #0 {
  %1 = alloca i32, align 4
  %2 = alloca i32, align 4
  %3 = alloca i32, align 4
  %4 = alloca i32, align 4
  %5 = alloca i32, align 4
  %6 = alloca i32, align 4
  %7 = load i32, ptr @High_Confidence, align 4
  %8 = icmp ne i32 %7, 0
  br i1 %8, label %9, label %15

9:                                                ; preds = %0
  %10 = load i32, ptr @Own_Tracked_Alt_Rate, align 4
  %11 = icmp sle i32 %10, 600
  br i1 %11, label %12, label %15

12:                                               ; preds = %9
  %13 = load i32, ptr @Cur_Vertical_Sep, align 4
  %14 = icmp sgt i32 %13, 600
  br label %15

15:                                               ; preds = %12, %9, %0
  %16 = phi i1 [ false, %9 ], [ false, %0 ], [ %14, %12 ]
  %17 = zext i1 %16 to i32
  store i32 %17, ptr %1, align 4
  %18 = load i32, ptr @Other_Capability, align 4
  %19 = icmp eq i32 %18, 1
  %20 = zext i1 %19 to i32
  store i32 %20, ptr %2, align 4
  %21 = load i32, ptr @Two_of_Three_Reports_Valid, align 4
  %22 = icmp ne i32 %21, 0
  br i1 %22, label %23, label %26

23:                                               ; preds = %15
  %24 = load i32, ptr @Other_RAC, align 4
  %25 = icmp eq i32 %24, 0
  br label %26

26:                                               ; preds = %23, %15
  %27 = phi i1 [ false, %15 ], [ %25, %23 ]
  %28 = zext i1 %27 to i32
  store i32 %28, ptr %3, align 4
  store i32 0, ptr %6, align 4
  %29 = load i32, ptr %1, align 4
  %30 = icmp ne i32 %29, 0
  br i1 %30, label %31, label %75

31:                                               ; preds = %26
  %32 = load i32, ptr %2, align 4
  %33 = icmp ne i32 %32, 0
  br i1 %33, label %34, label %37

34:                                               ; preds = %31
  %35 = load i32, ptr %3, align 4
  %36 = icmp ne i32 %35, 0
  br i1 %36, label %40, label %37

37:                                               ; preds = %34, %31
  %38 = load i32, ptr %2, align 4
  %39 = icmp ne i32 %38, 0
  br i1 %39, label %75, label %40

40:                                               ; preds = %37, %34
  %41 = call i32 @Non_Crossing_Biased_Climb()
  %42 = icmp ne i32 %41, 0
  br i1 %42, label %43, label %46

43:                                               ; preds = %40
  %44 = call i32 @Own_Below_Threat()
  %45 = icmp ne i32 %44, 0
  br label %46

46:                                               ; preds = %43, %40
  %47 = phi i1 [ false, %40 ], [ %45, %43 ]
  %48 = zext i1 %47 to i32
  store i32 %48, ptr %4, align 4
  %49 = call i32 @Non_Crossing_Biased_Descend()
  %50 = icmp ne i32 %49, 0
  br i1 %50, label %51, label %54

51:                                               ; preds = %46
  %52 = call i32 @Own_Above_Threat()
  %53 = icmp ne i32 %52, 0
  br label %54

54:                                               ; preds = %51, %46
  %55 = phi i1 [ false, %46 ], [ %53, %51 ]
  %56 = zext i1 %55 to i32
  store i32 %56, ptr %5, align 4
  %57 = load i32, ptr %4, align 4
  %58 = icmp ne i32 %57, 0
  br i1 %58, label %59, label %63

59:                                               ; preds = %54
  %60 = load i32, ptr %5, align 4
  %61 = icmp ne i32 %60, 0
  br i1 %61, label %62, label %63

62:                                               ; preds = %59
  store i32 0, ptr %6, align 4
  br label %74

63:                                               ; preds = %59, %54
  %64 = load i32, ptr %4, align 4
  %65 = icmp ne i32 %64, 0
  br i1 %65, label %66, label %67

66:                                               ; preds = %63
  store i32 1, ptr %6, align 4
  br label %73

67:                                               ; preds = %63
  %68 = load i32, ptr %5, align 4
  %69 = icmp ne i32 %68, 0
  br i1 %69, label %70, label %71

70:                                               ; preds = %67
  store i32 2, ptr %6, align 4
  br label %72

71:                                               ; preds = %67
  store i32 0, ptr %6, align 4
  br label %72

72:                                               ; preds = %71, %70
  br label %73

73:                                               ; preds = %72, %66
  br label %74

74:                                               ; preds = %73, %62
  br label %75

75:                                               ; preds = %74, %37, %26
  %76 = load i32, ptr %6, align 4
  ret i32 %76
}

; Function Attrs: noinline nounwind optnone ssp uwtable(sync)
define i32 @main(i32 noundef %0, ptr noundef %1) #0 {
  %3 = alloca i32, align 4
  %4 = alloca i32, align 4
  %5 = alloca ptr, align 8
  store i32 0, ptr %3, align 4
  store i32 %0, ptr %4, align 4
  store ptr %1, ptr %5, align 8
  %6 = load i32, ptr %4, align 4
  %7 = icmp slt i32 %6, 13
  br i1 %7, label %8, label %19

8:                                                ; preds = %2
  %9 = load ptr, ptr @__stdoutp, align 8
  %10 = call i32 (ptr, ptr, ...) @fprintf(ptr noundef %9, ptr noundef @.str) #4
  %11 = load ptr, ptr @__stdoutp, align 8
  %12 = call i32 (ptr, ptr, ...) @fprintf(ptr noundef %11, ptr noundef @.str.1) #4
  %13 = load ptr, ptr @__stdoutp, align 8
  %14 = call i32 (ptr, ptr, ...) @fprintf(ptr noundef %13, ptr noundef @.str.2) #4
  %15 = load ptr, ptr @__stdoutp, align 8
  %16 = call i32 (ptr, ptr, ...) @fprintf(ptr noundef %15, ptr noundef @.str.3) #4
  %17 = load ptr, ptr @__stdoutp, align 8
  %18 = call i32 (ptr, ptr, ...) @fprintf(ptr noundef %17, ptr noundef @.str.4) #4
  call void @exit(i32 noundef 1) #5
  unreachable

19:                                               ; preds = %2
  call void @initialize()
  %20 = load ptr, ptr %5, align 8
  %21 = getelementptr inbounds ptr, ptr %20, i64 1
  %22 = load ptr, ptr %21, align 8
  %23 = call i32 @atoi(ptr noundef %22)
  store i32 %23, ptr @Cur_Vertical_Sep, align 4
  %24 = load ptr, ptr %5, align 8
  %25 = getelementptr inbounds ptr, ptr %24, i64 2
  %26 = load ptr, ptr %25, align 8
  %27 = call i32 @atoi(ptr noundef %26)
  store i32 %27, ptr @High_Confidence, align 4
  %28 = load ptr, ptr %5, align 8
  %29 = getelementptr inbounds ptr, ptr %28, i64 3
  %30 = load ptr, ptr %29, align 8
  %31 = call i32 @atoi(ptr noundef %30)
  store i32 %31, ptr @Two_of_Three_Reports_Valid, align 4
  %32 = load ptr, ptr %5, align 8
  %33 = getelementptr inbounds ptr, ptr %32, i64 4
  %34 = load ptr, ptr %33, align 8
  %35 = call i32 @atoi(ptr noundef %34)
  store i32 %35, ptr @Own_Tracked_Alt, align 4
  %36 = load ptr, ptr %5, align 8
  %37 = getelementptr inbounds ptr, ptr %36, i64 5
  %38 = load ptr, ptr %37, align 8
  %39 = call i32 @atoi(ptr noundef %38)
  store i32 %39, ptr @Own_Tracked_Alt_Rate, align 4
  %40 = load ptr, ptr %5, align 8
  %41 = getelementptr inbounds ptr, ptr %40, i64 6
  %42 = load ptr, ptr %41, align 8
  %43 = call i32 @atoi(ptr noundef %42)
  store i32 %43, ptr @Other_Tracked_Alt, align 4
  %44 = load ptr, ptr %5, align 8
  %45 = getelementptr inbounds ptr, ptr %44, i64 7
  %46 = load ptr, ptr %45, align 8
  %47 = call i32 @atoi(ptr noundef %46)
  store i32 %47, ptr @Alt_Layer_Value, align 4
  %48 = load ptr, ptr %5, align 8
  %49 = getelementptr inbounds ptr, ptr %48, i64 8
  %50 = load ptr, ptr %49, align 8
  %51 = call i32 @atoi(ptr noundef %50)
  store i32 %51, ptr @Up_Separation, align 4
  %52 = load ptr, ptr %5, align 8
  %53 = getelementptr inbounds ptr, ptr %52, i64 9
  %54 = load ptr, ptr %53, align 8
  %55 = call i32 @atoi(ptr noundef %54)
  store i32 %55, ptr @Down_Separation, align 4
  %56 = load ptr, ptr %5, align 8
  %57 = getelementptr inbounds ptr, ptr %56, i64 10
  %58 = load ptr, ptr %57, align 8
  %59 = call i32 @atoi(ptr noundef %58)
  store i32 %59, ptr @Other_RAC, align 4
  %60 = load ptr, ptr %5, align 8
  %61 = getelementptr inbounds ptr, ptr %60, i64 11
  %62 = load ptr, ptr %61, align 8
  %63 = call i32 @atoi(ptr noundef %62)
  store i32 %63, ptr @Other_Capability, align 4
  %64 = load ptr, ptr %5, align 8
  %65 = getelementptr inbounds ptr, ptr %64, i64 12
  %66 = load ptr, ptr %65, align 8
  %67 = call i32 @atoi(ptr noundef %66)
  store i32 %67, ptr @Climb_Inhibit, align 4
  %68 = load ptr, ptr @__stdoutp, align 8
  %69 = call i32 @alt_sep_test()
  %70 = call i32 (ptr, ptr, ...) @fprintf(ptr noundef %68, ptr noundef @.str.5, i32 noundef %69) #4
  call void @exit(i32 noundef 0) #5
  unreachable
}

; Function Attrs: nounwind
declare i32 @fprintf(ptr noundef, ptr noundef, ...) #1

; Function Attrs: noreturn
declare void @exit(i32 noundef) #2

declare i32 @atoi(...) #3

attributes #0 = { noinline nounwind optnone ssp uwtable(sync) "frame-pointer"="non-leaf" "no-trapping-math"="true" "probe-stack"="__chkstk_darwin" "stack-protector-buffer-size"="8" "target-cpu"="apple-m1" "target-features"="+aes,+altnzcv,+bti,+ccdp,+ccidx,+complxnum,+crc,+dit,+dotprod,+flagm,+fp-armv8,+fp16fml,+fptoint,+fullfp16,+jsconv,+lse,+neon,+pauth,+perfmon,+predres,+ras,+rcpc,+rdm,+sb,+sha2,+sha3,+specrestrict,+ssbs,+v8.1a,+v8.2a,+v8.3a,+v8.4a,+v8.5a,+v8a,+zcm,+zcz" }
attributes #1 = { nounwind "frame-pointer"="non-leaf" "no-trapping-math"="true" "probe-stack"="__chkstk_darwin" "stack-protector-buffer-size"="8" "target-cpu"="apple-m1" "target-features"="+aes,+altnzcv,+bti,+ccdp,+ccidx,+complxnum,+crc,+dit,+dotprod,+flagm,+fp-armv8,+fp16fml,+fptoint,+fullfp16,+jsconv,+lse,+neon,+pauth,+perfmon,+predres,+ras,+rcpc,+rdm,+sb,+sha2,+sha3,+specrestrict,+ssbs,+v8.1a,+v8.2a,+v8.3a,+v8.4a,+v8.5a,+v8a,+zcm,+zcz" }
attributes #2 = { noreturn "frame-pointer"="non-leaf" "no-trapping-math"="true" "probe-stack"="__chkstk_darwin" "stack-protector-buffer-size"="8" "target-cpu"="apple-m1" "target-features"="+aes,+altnzcv,+bti,+ccdp,+ccidx,+complxnum,+crc,+dit,+dotprod,+flagm,+fp-armv8,+fp16fml,+fptoint,+fullfp16,+jsconv,+lse,+neon,+pauth,+perfmon,+predres,+ras,+rcpc,+rdm,+sb,+sha2,+sha3,+specrestrict,+ssbs,+v8.1a,+v8.2a,+v8.3a,+v8.4a,+v8.5a,+v8a,+zcm,+zcz" }
attributes #3 = { "frame-pointer"="non-leaf" "no-trapping-math"="true" "probe-stack"="__chkstk_darwin" "stack-protector-buffer-size"="8" "target-cpu"="apple-m1" "target-features"="+aes,+altnzcv,+bti,+ccdp,+ccidx,+complxnum,+crc,+dit,+dotprod,+flagm,+fp-armv8,+fp16fml,+fptoint,+fullfp16,+jsconv,+lse,+neon,+pauth,+perfmon,+predres,+ras,+rcpc,+rdm,+sb,+sha2,+sha3,+specrestrict,+ssbs,+v8.1a,+v8.2a,+v8.3a,+v8.4a,+v8.5a,+v8a,+zcm,+zcz" }
attributes #4 = { nounwind }
attributes #5 = { noreturn }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 2, !"SDK Version", [2 x i32] [i32 26, i32 0]}
!1 = !{i32 1, !"wchar_size", i32 4}
!2 = !{i32 8, !"PIC Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 1}
!4 = !{i32 7, !"frame-pointer", i32 1}
!5 = !{!"Apple clang version 17.0.0 (clang-1700.3.19.1)"}
