; Whitefoot conservative module
source_filename = "whitefoot"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

%wf.t.79689782061dec13 = type { i64, i64 }
%wf.t.88c85cf833d71e28.v0 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v1 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v2 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v3 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v4 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v5 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v6 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v7 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v8 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v9 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v10 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v11 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v13 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v14 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v15 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v16 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v17 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v18 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v19 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v20 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v21 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v22 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v23 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v24 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v25 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v26 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v27 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28.v28 = type { i32, i32, i8 }
%wf.t.88c85cf833d71e28 = type { i32, [8 x i8], [0 x %wf.t.88c85cf833d71e28.v0] }
%wf.t.996089250604052e = type { i32, %wf.t.88c85cf833d71e28 }
%wf.t.f3380055fe20f353 = type { i32, i64 }
%wf.t.07ce75c387735f4b = type { i32, i64 }
%wf.t.15b8e6e37e607262 = type { { i128, i128 }, { i128, i128 } }
%wf.t.3b1b6d56073edde7 = type { i32, %wf.t.88c85cf833d71e28 }
%wf.t.8656946ecebc34ec = type { { i128, i128 }, %wf.t.15b8e6e37e607262, { i128, i128 }, { i128, i128 }, { i128, i128 }, { i128, i128 }, { i128, i128 }, { i128, i128 } }
%wf.t.4f32c909b75cc77b = type { i32, { i128, i128 } }
%wf.t.050c23416549474d.v0 = type { i32, i64 }
%wf.t.050c23416549474d.v1 = type { i32, %wf.t.88c85cf833d71e28 }
%wf.t.050c23416549474d = type { i32, [12 x i8], [0 x %wf.t.050c23416549474d.v0] }
%wf.t.5b970ff2ad934046.v0 = type { i32, i64 }
%wf.t.5b970ff2ad934046.v1 = type { i32, %wf.t.996089250604052e }
%wf.t.5b970ff2ad934046 = type { i32, [20 x i8], [0 x %wf.t.5b970ff2ad934046.v0] }
%wf.t.8e49cf34abe1c006.v0 = type { i32, { i128, i128 } }
%wf.t.8e49cf34abe1c006.v1 = type { i32, i1 }
%wf.t.8e49cf34abe1c006 = type { i32, [44 x i8], [0 x %wf.t.8e49cf34abe1c006.v0] }
%wf.t.b80a9bfbd1f59cb4.v0 = type { i32, i64 }
%wf.t.b80a9bfbd1f59cb4.v1 = type { i32, %wf.t.f3380055fe20f353 }
%wf.t.b80a9bfbd1f59cb4 = type { i32, [20 x i8], [0 x %wf.t.b80a9bfbd1f59cb4.v0] }
%wf.t.4ef4128edabf98be = type { i32, i64, i1 }
%wf.t.f60af608c1958040.v0 = type { i32, i64 }
%wf.t.f60af608c1958040.v1 = type { i32, %wf.t.07ce75c387735f4b }
%wf.t.f60af608c1958040 = type { i32, [20 x i8], [0 x %wf.t.f60af608c1958040.v0] }
%wf.t.245242d1ce38c3e4.v0 = type { i32, { i128, i128 } }
%wf.t.245242d1ce38c3e4.v1 = type { i32, i1 }
%wf.t.245242d1ce38c3e4 = type { i32, [44 x i8], [0 x %wf.t.245242d1ce38c3e4.v0] }
%wf.t.0559b7ce3d6da8f1.v0 = type { i32, { i128, i128 } }
%wf.t.0559b7ce3d6da8f1.v1 = type { i32, %wf.t.88c85cf833d71e28 }
%wf.t.0559b7ce3d6da8f1 = type { i32, [44 x i8], [0 x %wf.t.0559b7ce3d6da8f1.v0] }
%wf.t.401891d75555d20e.v0 = type { i32, { i128, i128 } }
%wf.t.401891d75555d20e.v1 = type { i32, %wf.t.88c85cf833d71e28 }
%wf.t.401891d75555d20e = type { i32, [44 x i8], [0 x %wf.t.401891d75555d20e.v0] }
%wf.t.27caeb25122ac7c4.v0 = type { i32, { i128, i128 } }
%wf.t.27caeb25122ac7c4.v1 = type { i32, %wf.t.88c85cf833d71e28 }
%wf.t.27caeb25122ac7c4 = type { i32, [44 x i8], [0 x %wf.t.27caeb25122ac7c4.v0] }
%wf.t.6df397eafd3120ad.v0 = type { i32, i8 }
%wf.t.6df397eafd3120ad.v1 = type { i32, %wf.t.3b1b6d56073edde7 }
%wf.t.6df397eafd3120ad = type { i32, [16 x i8], [0 x %wf.t.6df397eafd3120ad.v0] }
%wf.t.8074de807c9b0e4e = type { %wf.t.6df397eafd3120ad, i64, i64 }
%wf.t.688872f0f831158e.v0 = type { i32, { i128, i128 } }
%wf.t.688872f0f831158e.v1 = type { i32, %wf.t.88c85cf833d71e28 }
%wf.t.688872f0f831158e = type { i32, [44 x i8], [0 x %wf.t.688872f0f831158e.v0] }
%wf.t.93559409a7432998.v0 = type { i32, i8 }
%wf.t.93559409a7432998.v1 = type { i32, %wf.t.88c85cf833d71e28 }
%wf.t.93559409a7432998 = type { i32, [12 x i8], [0 x %wf.t.93559409a7432998.v0] }

@.wf_resource.heap = private unnamed_addr constant [20 x i8] c"\7B\22\72\65\73\6F\75\72\63\65\22\3A\22\68\65\61\70\22\7D\0A", align 1
declare i64 @write(i32, ptr, i64)
declare ptr @__errno_location()

define private i64 @wf_resource_write(ptr %bytes, i64 %length) #0 align 64 {
entry:
  br label %write
write:
  %written = call i64 @write(i32 2, ptr %bytes, i64 %length)
  %failed = icmp slt i64 %written, 0
  br i1 %failed, label %error, label %done
error:
  %errno = call ptr @__errno_location()
  %code = load i32, ptr %errno, align 4
  %interrupted = icmp eq i32 %code, 4
  br i1 %interrupted, label %write, label %done
done:
  ret i64 %written
}

declare void @abort() noreturn
declare ptr @malloc(i64)
declare void @free(ptr)

define private void @wf_resource_record_abort(ptr %message, i64 %length) noreturn #0 align 64 {
entry:
  br label %write.loop
write.loop:
  %cursor = phi ptr [ %message, %entry ], [ %next, %write.more ]
  %remaining = phi i64 [ %length, %entry ], [ %left, %write.more ]
  %written = call i64 @wf_resource_write(ptr %cursor, i64 %remaining)
  %complete = icmp eq i64 %written, %remaining
  br i1 %complete, label %abort, label %write.incomplete
write.incomplete:
  %progress = icmp sgt i64 %written, 0
  br i1 %progress, label %write.more, label %abort
write.more:
  %next = getelementptr i8, ptr %cursor, i64 %written
  %left = sub i64 %remaining, %written
  br label %write.loop
abort:
  call void @abort()
  unreachable
}

define private void @wf_resource_abort() noreturn #0 align 64 {
entry:
  call void @wf_resource_record_abort(ptr @.wf_resource.heap, i64 20)
  unreachable
}

define private void @wf.drop.run.446072896286209a(ptr %value) #0 align 64 {
entry:
  %len = load i64, ptr %value
  %cap.ptr = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %value, i32 0, i32 1
  %cap = load i64, ptr %cap.ptr
  %dir.ptr = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %value, i32 0, i32 2
  %dir = load ptr, ptr %dir.ptr
  br label %pages.start
pages.start:
  %quotient = lshr i64 %cap, 8
  %remainder = and i64 %cap, 255
  %partial = icmp ne i64 %remainder, 0
  %carry = zext i1 %partial to i64
  %count = add nuw i64 %quotient, %carry
  br label %pages
pages:
  %p = phi i64 [ 0, %pages.start ], [ %p.next, %page.free ]
  %allocated = icmp ult i64 %p, %count
  br i1 %allocated, label %page.free, label %directory.free
page.free:
  %slot = getelementptr inbounds ptr, ptr %dir, i64 %p
  %allocation = load ptr, ptr %slot
  call void @free(ptr %allocation)
  %p.next = add nuw i64 %p, 1
  br label %pages
directory.free:
  call void @free(ptr %dir)
  ret void
}

declare void @llvm.memmove.p0.p0.i64(ptr, ptr, i64, i1 immarg)
declare { i64, i1 } @llvm.uadd.with.overflow.i64(i64, i64)
declare { i64, i1 } @llvm.umul.with.overflow.i64(i64, i64)

define i64 @wf_change(ptr noalias nonnull captures(none) dereferenceable(8) %v0, i64 %v1) #0 align 64 {
entry:
  %v2 = load i64, ptr %v0
  %v3 = add i64 %v2, %v1
  store i64 %v3, ptr %v0
  ret i64 %v2
}

define i8 @wf_grow_directory(ptr noalias nonnull captures(none) dereferenceable(8) %v0) #0 align 64 {
entry:
  %t0 = load ptr, ptr %v0
  %v1 = getelementptr i8, ptr %t0, i64 0
  %t2 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v1, i32 0, i32 1
  %t1 = load i64, ptr %t2
  %v2 = add i64 %t1, 0
  %v3 = select i1 true, i64 1024, i64 1024
  %v4 = icmp ule i64 %v2, %v3
  switch i1 %v4, label %invalid.tag.b0 [
    i1 1, label %bb2
    i1 0, label %bb3
  ]
invalid.tag.b0:
  unreachable
bb1:
  %v5 = phi ptr [ %v0, %bb2 ], [ %v0, %bb3 ]
  %v6 = phi i64 [ %v2, %bb2 ], [ %v2, %bb3 ]
  %v9 = select i1 true, i8 0, i8 0
  ret i8 %v9
bb2:
  %v7 = select i1 true, i64 1024, i64 1024
  %v8 = call i8 @wf_grow_paged$instance$ed4950029184679a(ptr %v0, i64 %v7)
  br label %bb1
bb3:
  br label %bb1
}

define i8 @wf_flat_slots(ptr noalias nonnull captures(none) dereferenceable(8) %v0) #0 align 64 {
entry:
  %t0 = load ptr, ptr %v0
  %v1 = getelementptr i8, ptr %t0, i64 0
  %t2 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v1, i32 0, i32 0
  %t1 = load i64, ptr %t2
  %v2 = add i64 %t1, 0
  %v3 = select i1 true, i64 0, i64 0
  br label %bb1
bb1:
  %v4 = phi ptr [ %v0, %entry ], [ %v17, %bb5 ]
  %v5 = phi i64 [ %v2, %entry ], [ %v18, %bb5 ]
  %v6 = phi i64 [ %v3, %entry ], [ %v19, %bb5 ]
  %v7 = phi i64 [ %v2, %entry ], [ %v20, %bb5 ]
  %v8 = phi i64 [ %v3, %entry ], [ %v23, %bb5 ]
  %v11 = icmp ult i64 %v8, %v7
  switch i1 %v11, label %invalid.tag.b1 [
    i1 1, label %bb2
    i1 0, label %bb3
  ]
invalid.tag.b1:
  unreachable
bb2:
  %t3 = load ptr, ptr %v4
  %v12 = getelementptr i8, ptr %t3, i64 0
  %t4 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v12, i32 0, i32 2
  %t5 = load ptr, ptr %t4
  %t6 = lshr i64 %v8, 8
  %t7 = and i64 %v8, 255
  %t8 = getelementptr inbounds ptr, ptr %t5, i64 %t6
  %t9 = load ptr, ptr %t8
  %t10 = getelementptr inbounds %wf.t.79689782061dec13, ptr %t9, i64 %t7
  %v13 = getelementptr i8, ptr %t10, i64 0
  %t11 = getelementptr inbounds %wf.t.79689782061dec13, ptr %v13, i32 0, i32 0
  %v14 = getelementptr i8, ptr %t11, i64 0
  %v15 = select i1 true, i64 10, i64 10
  %v16 = call i64 @wf_change(ptr %v14, i64 %v15)
  br label %bb5
bb3:
  br label %bb4
bb4:
  %v9 = phi ptr [ %v4, %bb3 ]
  %v10 = phi i64 [ %v5, %bb3 ]
  %v24 = select i1 true, i8 0, i8 0
  ret i8 %v24
bb5:
  %v17 = phi ptr [ %v4, %bb2 ]
  %v18 = phi i64 [ %v5, %bb2 ]
  %v19 = phi i64 [ %v6, %bb2 ]
  %v20 = phi i64 [ %v7, %bb2 ]
  %v21 = phi i64 [ %v8, %bb2 ]
  %v22 = select i1 true, i64 1, i64 1
  %v23 = add i64 %v21, %v22
  br label %bb1
}

define i8 @wf_one_page(ptr noalias nonnull captures(none) %wf.arg.v0.data, i64 %wf.arg.v0.len) #0 align 64 {
entry:
  %v0.data = insertvalue { ptr, i64 } poison, ptr %wf.arg.v0.data, 0
  %v0 = insertvalue { ptr, i64 } %v0.data, i64 %wf.arg.v0.len, 1
  %v1 = extractvalue { ptr, i64 } %v0, 1
  %v2 = select i1 true, i64 0, i64 0
  br label %bb1
bb1:
  %v3 = phi { ptr, i64 } [ %v0, %entry ], [ %v15, %bb5 ]
  %v4 = phi i64 [ %v1, %entry ], [ %v16, %bb5 ]
  %v5 = phi i64 [ %v2, %entry ], [ %v17, %bb5 ]
  %v6 = phi i64 [ %v1, %entry ], [ %v18, %bb5 ]
  %v7 = phi i64 [ %v2, %entry ], [ %v21, %bb5 ]
  %v10 = icmp ult i64 %v7, %v6
  switch i1 %v10, label %invalid.tag.b1 [
    i1 1, label %bb2
    i1 0, label %bb3
  ]
invalid.tag.b1:
  unreachable
bb2:
  %t0 = extractvalue { ptr, i64 } %v3, 0
  %v11 = getelementptr inbounds %wf.t.79689782061dec13, ptr %t0, i64 %v7
  %t1 = getelementptr inbounds %wf.t.79689782061dec13, ptr %v11, i32 0, i32 0
  %v12 = getelementptr i8, ptr %t1, i64 0
  %v13 = select i1 true, i64 100, i64 100
  %v14 = call i64 @wf_change(ptr %v12, i64 %v13)
  br label %bb5
bb3:
  br label %bb4
bb4:
  %v8 = phi { ptr, i64 } [ %v3, %bb3 ]
  %v9 = phi i64 [ %v4, %bb3 ]
  %v22 = select i1 true, i8 0, i8 0
  ret i8 %v22
bb5:
  %v15 = phi { ptr, i64 } [ %v3, %bb2 ]
  %v16 = phi i64 [ %v4, %bb2 ]
  %v17 = phi i64 [ %v5, %bb2 ]
  %v18 = phi i64 [ %v6, %bb2 ]
  %v19 = phi i64 [ %v7, %bb2 ]
  %v20 = select i1 true, i64 1, i64 1
  %v21 = add i64 %v19, %v20
  br label %bb1
}

define i8 @wf_by_page(ptr noalias nonnull captures(none) dereferenceable(8) %v0) #0 align 64 {
entry:
  %t0 = load ptr, ptr %v0
  %v1 = getelementptr i8, ptr %t0, i64 0
  %t2 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v1, i32 0, i32 0
  %t1 = load i64, ptr %t2
  %t3 = lshr i64 %t1, 8
  %t4 = and i64 %t1, 255
  %t5 = icmp ne i64 %t4, 0
  %t6 = zext i1 %t5 to i64
  %t7 = add nuw i64 %t3, %t6
  %v2 = add i64 %t7, 0
  %v3 = select i1 true, i64 0, i64 0
  br label %bb1
bb1:
  %v4 = phi ptr [ %v0, %entry ], [ %v15, %bb5 ]
  %v5 = phi i64 [ %v2, %entry ], [ %v16, %bb5 ]
  %v6 = phi i64 [ %v3, %entry ], [ %v17, %bb5 ]
  %v7 = phi i64 [ %v2, %entry ], [ %v18, %bb5 ]
  %v8 = phi i64 [ %v3, %entry ], [ %v21, %bb5 ]
  %v11 = icmp ult i64 %v8, %v7
  switch i1 %v11, label %invalid.tag.b1 [
    i1 1, label %bb2
    i1 0, label %bb3
  ]
invalid.tag.b1:
  unreachable
bb2:
  %t8 = load ptr, ptr %v4
  %v12 = getelementptr i8, ptr %t8, i64 0
  %t9 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v12, i32 0, i32 2
  %t10 = load ptr, ptr %t9
  %t11 = getelementptr inbounds ptr, ptr %t10, i64 %v8
  %t12 = load ptr, ptr %t11
  %t13 = load i64, ptr %v12
  %t14 = shl nuw i64 %v8, 8
  %t15 = sub nuw i64 %t13, %t14
  %t16 = icmp uge i64 %t15, 256
  %t17 = select i1 %t16, i64 256, i64 %t15
  %t18 = insertvalue { ptr, i64 } poison, ptr %t12, 0
  %v13 = insertvalue { ptr, i64 } %t18, i64 %t17, 1
  %t19 = extractvalue { ptr, i64 } %v13, 0
  %t20 = extractvalue { ptr, i64 } %v13, 1
  %v14 = call i8 @wf_one_page(ptr %t19, i64 %t20)
  br label %bb5
bb3:
  br label %bb4
bb4:
  %v9 = phi ptr [ %v4, %bb3 ]
  %v10 = phi i64 [ %v5, %bb3 ]
  %v22 = select i1 true, i8 0, i8 0
  ret i8 %v22
bb5:
  %v15 = phi ptr [ %v4, %bb2 ]
  %v16 = phi i64 [ %v5, %bb2 ]
  %v17 = phi i64 [ %v6, %bb2 ]
  %v18 = phi i64 [ %v7, %bb2 ]
  %v19 = phi i64 [ %v8, %bb2 ]
  %v20 = select i1 true, i64 1, i64 1
  %v21 = add i64 %v19, %v20
  br label %bb1
}

define void @wf_main(ptr %wf.result) #0 align 64 {
entry:
  %wf.slot.0 = alloca %wf.t.79689782061dec13, align 8
  %wf.slot.1 = alloca %wf.t.79689782061dec13, align 8
  %v8 = alloca ptr, align 8
  %v0 = call i64 @wf_paged_page_len$instance$ed4950029184679a()
  %v1 = select i1 true, i64 256, i64 256
  %v2 = icmp ne i64 %v0, %v1
  switch i1 %v2, label %invalid.tag.b0 [
    i1 1, label %bb2
    i1 0, label %bb3
  ]
invalid.tag.b0:
  unreachable
bb1:
  %v3 = phi i64 [ %v0, %bb3 ]
  %v6 = select i1 true, i64 1, i64 1
  %v7 = call ptr @wf_box_paged_new$instance$ed4950029184679a(i64 %v6)
  store ptr %v7, ptr %v8
  %v9 = select i1 true, i64 0, i64 0
  %v10 = select i1 true, i64 99, i64 99
  store %wf.t.79689782061dec13 zeroinitializer, ptr %wf.slot.0
  %t0 = getelementptr inbounds %wf.t.79689782061dec13, ptr %wf.slot.0, i32 0, i32 0
  store i64 %v9, ptr %t0
  %t1 = getelementptr inbounds %wf.t.79689782061dec13, ptr %wf.slot.0, i32 0, i32 1
  store i64 %v10, ptr %t1
  %t2 = load ptr, ptr %v8
  %v12 = getelementptr i8, ptr %t2, i64 0
  %v13 = call i8 @wf_place_back$instance$dacaeb1c2706d0db(ptr %v12, ptr %wf.slot.0)
  %v14 = call i8 @wf_grow_directory(ptr %v8)
  %v15 = select i1 true, i64 1, i64 1
  %v16 = select i1 true, i64 768, i64 768
  br label %bb4
bb2:
  %v4 = select i1 true, i8 1, i8 1
  call void @wf_std.process.exit_status(ptr %wf.result, i8 %v4)
  ret void
bb3:
  br label %bb1
bb4:
  %v17 = phi i64 [ %v3, %bb1 ], [ %v42, %bb11 ]
  %v18 = phi ptr [ %v8, %bb1 ], [ %v43, %bb11 ]
  %v20 = phi i64 [ %v15, %bb1 ], [ %v45, %bb11 ]
  %v21 = phi i64 [ %v16, %bb1 ], [ %v46, %bb11 ]
  %v22 = phi i64 [ %v15, %bb1 ], [ %v49, %bb11 ]
  %v26 = icmp ult i64 %v22, %v21
  switch i1 %v26, label %invalid.tag.b4 [
    i1 1, label %bb5
    i1 0, label %bb6
  ]
invalid.tag.b4:
  unreachable
bb5:
  %t3 = load ptr, ptr %v18
  %v27 = getelementptr i8, ptr %t3, i64 0
  %t5 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v27, i32 0, i32 0
  %t4 = load i64, ptr %t5
  %v28 = add i64 %t4, 0
  %t6 = load ptr, ptr %v18
  %v29 = getelementptr i8, ptr %t6, i64 0
  %t8 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v29, i32 0, i32 1
  %t7 = load i64, ptr %t8
  %v30 = add i64 %t7, 0
  %v31 = icmp ult i64 %v28, %v30
  switch i1 %v31, label %invalid.tag.b5 [
    i1 1, label %bb9
    i1 0, label %bb10
  ]
invalid.tag.b5:
  unreachable
bb6:
  br label %bb7
bb7:
  %v23 = phi i64 [ %v17, %bb6 ]
  %v24 = phi ptr [ %v18, %bb6 ]
  %v50 = call i8 @wf_flat_slots(ptr %v24)
  %v51 = call i8 @wf_by_page(ptr %v24)
  %t9 = load ptr, ptr %v24
  %v52 = getelementptr i8, ptr %t9, i64 0
  %t11 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v52, i32 0, i32 0
  %t10 = load i64, ptr %t11
  %v53 = add i64 %t10, 0
  %v54 = select i1 true, i64 768, i64 768
  %v55 = icmp ne i64 %v53, %v54
  switch i1 %v55, label %invalid.tag.b7 [
    i1 1, label %bb13
    i1 0, label %bb14
  ]
invalid.tag.b7:
  unreachable
bb8:
  %v32 = phi i64 [ %v17, %bb9 ]
  %v33 = phi ptr [ %v18, %bb9 ]
  %v35 = phi i64 [ %v22, %bb9 ]
  br label %bb11
bb9:
  %v36 = select i1 true, i64 99, i64 99
  store %wf.t.79689782061dec13 zeroinitializer, ptr %wf.slot.1
  %t12 = getelementptr inbounds %wf.t.79689782061dec13, ptr %wf.slot.1, i32 0, i32 0
  store i64 %v22, ptr %t12
  %t13 = getelementptr inbounds %wf.t.79689782061dec13, ptr %wf.slot.1, i32 0, i32 1
  store i64 %v36, ptr %t13
  %t14 = load ptr, ptr %v18
  %v38 = getelementptr i8, ptr %t14, i64 0
  %v39 = call i8 @wf_place_back$instance$dacaeb1c2706d0db(ptr %v38, ptr %wf.slot.1)
  br label %bb8
bb10:
  %v40 = select i1 true, i8 6, i8 6
  call void @wf_std.process.exit_status(ptr %wf.result, i8 %v40)
  %t15 = load ptr, ptr %v18
  call void @wf.drop.run.446072896286209a(ptr %t15)
  call void @free(ptr %t15)
  ; drop %v18
  ret void
bb11:
  %v42 = phi i64 [ %v32, %bb8 ]
  %v43 = phi ptr [ %v33, %bb8 ]
  %v45 = phi i64 [ %v20, %bb8 ]
  %v46 = phi i64 [ %v21, %bb8 ]
  %v47 = phi i64 [ %v22, %bb8 ]
  %v48 = select i1 true, i64 1, i64 1
  %v49 = add i64 %v47, %v48
  br label %bb4
bb12:
  %v56 = phi i64 [ %v23, %bb14 ]
  %v57 = phi ptr [ %v24, %bb14 ]
  %t16 = load ptr, ptr %v57
  %v61 = getelementptr i8, ptr %t16, i64 0
  %t18 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v61, i32 0, i32 0
  %t17 = load i64, ptr %t18
  %t19 = lshr i64 %t17, 8
  %t20 = and i64 %t17, 255
  %t21 = icmp ne i64 %t20, 0
  %t22 = zext i1 %t21 to i64
  %t23 = add nuw i64 %t19, %t22
  %v62 = add i64 %t23, 0
  %v63 = select i1 true, i64 3, i64 3
  %v64 = icmp ne i64 %v62, %v63
  switch i1 %v64, label %invalid.tag.b12 [
    i1 1, label %bb16
    i1 0, label %bb17
  ]
invalid.tag.b12:
  unreachable
bb13:
  %v59 = select i1 true, i8 2, i8 2
  call void @wf_std.process.exit_status(ptr %wf.result, i8 %v59)
  %t24 = load ptr, ptr %v24
  call void @wf.drop.run.446072896286209a(ptr %t24)
  call void @free(ptr %t24)
  ; drop %v24
  ret void
bb14:
  br label %bb12
bb15:
  %v65 = phi i64 [ %v56, %bb17 ]
  %v66 = phi ptr [ %v57, %bb17 ]
  %v70 = select i1 true, i64 0, i64 0
  %t25 = load ptr, ptr %v66
  %v71 = getelementptr i8, ptr %t25, i64 0
  %t27 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v71, i32 0, i32 0
  %t26 = load i64, ptr %t27
  %v72 = add i64 %t26, 0
  br label %bb18
bb16:
  %v68 = select i1 true, i8 3, i8 3
  call void @wf_std.process.exit_status(ptr %wf.result, i8 %v68)
  %t28 = load ptr, ptr %v57
  call void @wf.drop.run.446072896286209a(ptr %t28)
  call void @free(ptr %t28)
  ; drop %v57
  ret void
bb17:
  br label %bb15
bb18:
  %v73 = phi i64 [ %v65, %bb15 ], [ %v110, %bb28 ]
  %v74 = phi ptr [ %v66, %bb15 ], [ %v111, %bb28 ]
  %v76 = phi i64 [ %v70, %bb15 ], [ %v113, %bb28 ]
  %v77 = phi i64 [ %v72, %bb15 ], [ %v114, %bb28 ]
  %v78 = phi i64 [ %v70, %bb15 ], [ %v117, %bb28 ]
  %v82 = icmp ult i64 %v78, %v77
  switch i1 %v82, label %invalid.tag.b18 [
    i1 1, label %bb19
    i1 0, label %bb20
  ]
invalid.tag.b18:
  unreachable
bb19:
  %v83 = select i1 true, i64 110, i64 110
  %v84 = add i64 %v78, %v83
  %t29 = load ptr, ptr %v74
  %v85 = getelementptr i8, ptr %t29, i64 0
  %t30 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v85, i32 0, i32 2
  %t31 = load ptr, ptr %t30
  %t32 = lshr i64 %v78, 8
  %t33 = and i64 %v78, 255
  %t34 = getelementptr inbounds ptr, ptr %t31, i64 %t32
  %t35 = load ptr, ptr %t34
  %t36 = getelementptr inbounds %wf.t.79689782061dec13, ptr %t35, i64 %t33
  %v86 = getelementptr i8, ptr %t36, i64 0
  %t37 = getelementptr inbounds %wf.t.79689782061dec13, ptr %v86, i32 0, i32 0
  %v87 = getelementptr i8, ptr %t37, i64 0
  %v88 = load i64, ptr %v87
  %v89 = icmp ne i64 %v88, %v84
  switch i1 %v89, label %invalid.tag.b19 [
    i1 1, label %bb23
    i1 0, label %bb24
  ]
invalid.tag.b19:
  unreachable
bb20:
  br label %bb21
bb21:
  %v79 = phi i64 [ %v73, %bb20 ]
  %v80 = phi ptr [ %v74, %bb20 ]
  %v118 = select i1 true, i8 0, i8 0
  call void @wf_std.process.exit_status(ptr %wf.result, i8 %v118)
  %t38 = load ptr, ptr %v80
  call void @wf.drop.run.446072896286209a(ptr %t38)
  call void @free(ptr %t38)
  ; drop %v80
  ret void
bb22:
  %v90 = phi i64 [ %v73, %bb24 ]
  %v91 = phi ptr [ %v74, %bb24 ]
  %v93 = phi i64 [ %v78, %bb24 ]
  %v94 = phi i64 [ %v84, %bb24 ]
  %t39 = load ptr, ptr %v91
  %v97 = getelementptr i8, ptr %t39, i64 0
  %t40 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v97, i32 0, i32 2
  %t41 = load ptr, ptr %t40
  %t42 = lshr i64 %v93, 8
  %t43 = and i64 %v93, 255
  %t44 = getelementptr inbounds ptr, ptr %t41, i64 %t42
  %t45 = load ptr, ptr %t44
  %t46 = getelementptr inbounds %wf.t.79689782061dec13, ptr %t45, i64 %t43
  %v98 = getelementptr i8, ptr %t46, i64 0
  %t47 = getelementptr inbounds %wf.t.79689782061dec13, ptr %v98, i32 0, i32 1
  %v99 = getelementptr i8, ptr %t47, i64 0
  %v100 = load i64, ptr %v99
  %v101 = select i1 true, i64 99, i64 99
  %v102 = icmp ne i64 %v100, %v101
  switch i1 %v102, label %invalid.tag.b22 [
    i1 1, label %bb26
    i1 0, label %bb27
  ]
invalid.tag.b22:
  unreachable
bb23:
  %v95 = select i1 true, i8 4, i8 4
  call void @wf_std.process.exit_status(ptr %wf.result, i8 %v95)
  %t48 = load ptr, ptr %v74
  call void @wf.drop.run.446072896286209a(ptr %t48)
  call void @free(ptr %t48)
  ; drop %v74
  ret void
bb24:
  br label %bb22
bb25:
  %v103 = phi i64 [ %v90, %bb27 ]
  %v104 = phi ptr [ %v91, %bb27 ]
  %v106 = phi i64 [ %v93, %bb27 ]
  %v107 = phi i64 [ %v94, %bb27 ]
  br label %bb28
bb26:
  %v108 = select i1 true, i8 5, i8 5
  call void @wf_std.process.exit_status(ptr %wf.result, i8 %v108)
  %t49 = load ptr, ptr %v91
  call void @wf.drop.run.446072896286209a(ptr %t49)
  call void @free(ptr %t49)
  ; drop %v91
  ret void
bb27:
  br label %bb25
bb28:
  %v110 = phi i64 [ %v103, %bb25 ]
  %v111 = phi ptr [ %v104, %bb25 ]
  %v113 = phi i64 [ %v76, %bb25 ]
  %v114 = phi i64 [ %v77, %bb25 ]
  %v115 = phi i64 [ %v78, %bb25 ]
  %v116 = select i1 true, i64 1, i64 1
  %v117 = add i64 %v115, %v116
  br label %bb18
}

declare void @wf_std.time.clock_share(ptr %wf.result, ptr noalias nonnull captures(none) dereferenceable(32) %v0)

declare void @wf_std.time.wall_clock_share(ptr %wf.result, ptr noalias nonnull captures(none) dereferenceable(32) %v0)

declare void @wf_std.time.now(ptr %wf.result, ptr noalias nonnull captures(none) dereferenceable(32) %v0)

declare void @wf_std.time.instant_after(ptr %wf.result, ptr %wf.arg.v0, i64 %v1)

declare i64 @wf_std.time.nanoseconds_from(ptr %wf.arg.v0, ptr %wf.arg.v1)

declare i1 @wf_std.time.instant_reached(ptr %wf.arg.v0, ptr %wf.arg.v1)

declare i32 @wf_std.time.sleep_until.start(ptr %wf.result, ptr %wf.arg.v0, ptr %wf.operation)
declare void @wf_std.time.sleep_until.finish(ptr %wf.result, ptr %wf.arg.v0, ptr %wf.operation)

declare i64 @wf_std.time.unix_nanoseconds(ptr noalias nonnull captures(none) dereferenceable(32) %v0)

declare void @wf_std.io.factory_share(ptr %wf.result, ptr noalias nonnull captures(none) dereferenceable(32) %v0)

declare i32 @wf_std.io.write_once.start(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.arg.v2.data, i64 %wf.arg.v2.len, i64 %v3, i64 %v4, ptr %wf.arg.v5, ptr %wf.operation)
declare void @wf_std.io.write_once.finish(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.arg.v2.data, i64 %wf.arg.v2.len, i64 %v3, i64 %v4, ptr %wf.arg.v5, ptr %wf.operation)

declare i32 @wf_std.io.read_next.start(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.arg.v2.data, i64 %wf.arg.v2.len, i64 %v3, i64 %v4, ptr %wf.arg.v5, ptr %wf.operation)
declare void @wf_std.io.read_next.finish(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.arg.v2.data, i64 %wf.arg.v2.len, i64 %v3, i64 %v4, ptr %wf.arg.v5, ptr %wf.operation)

declare i64 @wf_std.text.args_count(ptr noalias nonnull captures(none) dereferenceable(32) %v0)

declare void @wf_std.text.arg_get(ptr %wf.result, ptr noalias nonnull captures(none) dereferenceable(32) %v0, i64 %v1)

declare i64 @wf_std.text.host_bytes_len(ptr noalias nonnull captures(none) dereferenceable(32) %v0)

declare void @wf_std.text.host_copy_bytes(ptr %wf.result, ptr noalias nonnull captures(none) dereferenceable(32) %v0, ptr noalias nonnull captures(none) %wf.arg.v1.data, i64 %wf.arg.v1.len, i64 %v2, i64 %v3)

declare %wf.t.4ef4128edabf98be @wf_std.text.host_utf8_len(ptr noalias nonnull captures(none) dereferenceable(32) %v0)

declare void @wf_std.text.host_copy_utf8(ptr %wf.result, ptr noalias nonnull captures(none) dereferenceable(32) %v0, ptr noalias nonnull captures(none) %wf.arg.v1.data, i64 %wf.arg.v1.len, i64 %v2, i64 %v3)

declare void @wf_std.fs.relative_path(ptr %wf.result, ptr %wf.arg.v0)

declare i32 @wf_std.fs.open_read.start(ptr %wf.result, ptr %v0, ptr %v1, ptr %v2, ptr %wf.operation)
declare void @wf_std.fs.open_read.finish(ptr %wf.result, ptr %v0, ptr %v1, ptr %v2, ptr %wf.operation)

declare i32 @wf_std.fs.read_at.start(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.arg.v2.data, i64 %wf.arg.v2.len, i64 %v3, i64 %v4, i64 %v5, ptr %wf.operation)
declare void @wf_std.fs.read_at.finish(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.arg.v2.data, i64 %wf.arg.v2.len, i64 %v3, i64 %v4, i64 %v5, ptr %wf.operation)

declare i32 @wf_std.fs.open_directory.start(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.arg.v2.data, i64 %wf.arg.v2.len, i64 %v3, i64 %v4, ptr %wf.operation)
declare void @wf_std.fs.open_directory.finish(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.arg.v2.data, i64 %wf.arg.v2.len, i64 %v3, i64 %v4, ptr %wf.operation)

declare i32 @wf_std.fs.open_directory_source.start(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.operation)
declare void @wf_std.fs.open_directory_source.finish(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.operation)

declare i32 @wf_std.fs.directory_next.start(ptr %wf.result, ptr %v0, ptr %wf.arg.v1.data, i64 %wf.arg.v1.len, i64 %v2, i64 %v3, ptr %wf.operation)
declare void @wf_std.fs.directory_next.finish(ptr %wf.result, ptr %v0, ptr %wf.arg.v1.data, i64 %wf.arg.v1.len, i64 %v2, i64 %v3, ptr %wf.operation)

declare i32 @wf_std.fs.open_file.start(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.arg.v2.data, i64 %wf.arg.v2.len, i64 %v3, i64 %v4, ptr %wf.operation)
declare void @wf_std.fs.open_file.finish(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.arg.v2.data, i64 %wf.arg.v2.len, i64 %v3, i64 %v4, ptr %wf.operation)

declare i32 @wf_std.fs.open_append.start(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.arg.v2.data, i64 %wf.arg.v2.len, i64 %v3, i64 %v4, ptr %wf.operation)
declare void @wf_std.fs.open_append.finish(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.arg.v2.data, i64 %wf.arg.v2.len, i64 %v3, i64 %v4, ptr %wf.operation)

declare i32 @wf_std.fs.append_once.start(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.arg.v2.data, i64 %wf.arg.v2.len, i64 %v3, i64 %v4, ptr %wf.operation)
declare void @wf_std.fs.append_once.finish(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.arg.v2.data, i64 %wf.arg.v2.len, i64 %v3, i64 %v4, ptr %wf.operation)

declare i32 @wf_std.fs.sync_file.start(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.operation)
declare void @wf_std.fs.sync_file.finish(ptr %wf.result, ptr %v0, ptr %v1, ptr %wf.operation)

declare i32 @wf_std.fs.truncate_file.start(ptr %wf.result, ptr %v0, ptr %v1, i64 %v2, ptr %wf.operation)
declare void @wf_std.fs.truncate_file.finish(ptr %wf.result, ptr %v0, ptr %v1, i64 %v2, ptr %wf.operation)

declare i32 @wf_std.fs.close_read.start(ptr %wf.result, ptr %v0, ptr %wf.arg.v1, ptr %wf.operation)
declare void @wf_std.fs.close_read.finish(ptr %wf.result, ptr %v0, ptr %wf.arg.v1, ptr %wf.operation)

declare i32 @wf_std.fs.close_write.start(ptr %wf.result, ptr %v0, ptr %wf.arg.v1, ptr %wf.operation)
declare void @wf_std.fs.close_write.finish(ptr %wf.result, ptr %v0, ptr %wf.arg.v1, ptr %wf.operation)

declare i32 @wf_std.fs.close_directory.start(ptr %wf.result, ptr %v0, ptr %wf.arg.v1, ptr %wf.operation)
declare void @wf_std.fs.close_directory.finish(ptr %wf.result, ptr %v0, ptr %wf.arg.v1, ptr %wf.operation)

declare i32 @wf_std.fs.close_directory_write.start(ptr %wf.result, ptr %v0, ptr %wf.arg.v1, ptr %wf.operation)
declare void @wf_std.fs.close_directory_write.finish(ptr %wf.result, ptr %v0, ptr %wf.arg.v1, ptr %wf.operation)

declare i32 @wf_std.fs.close_directory_source.start(ptr %wf.result, ptr %v0, ptr %wf.arg.v1, ptr %wf.operation)
declare void @wf_std.fs.close_directory_source.finish(ptr %wf.result, ptr %v0, ptr %wf.arg.v1, ptr %wf.operation)

declare void @wf_std.process.exit_status(ptr %wf.result, i8 %v0)

define i64 @wf_paged_page_len$instance$ed4950029184679a() #0 align 64 {
entry:
  %v0 = select i1 true, i64 256, i64 256
  ret i64 %v0
}

define ptr @wf_box_paged_new$instance$ed4950029184679a(i64 %v0) #0 align 64 {
entry:
  %t0 = call ptr @malloc(i64 32)
  %t1 = icmp ne ptr %t0, null
  br i1 %t1, label %paged.alloc.t0, label %paged.oom.v1
paged.alloc.t0:
  %t2 = call ptr @malloc(i64 8)
  %t3 = icmp ne ptr %t2, null
  br i1 %t3, label %paged.alloc.t2, label %paged.oom.v1
paged.alloc.t2:
  %t4 = insertvalue { i64, i64, ptr, i64 } { i64 0, i64 0, ptr null, i64 1 }, ptr %t2, 2
  store { i64, i64, ptr, i64 } %t4, ptr %t0
  %t5 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %t0, i32 0, i32 1
  %t6 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %t0, i32 0, i32 2
  %t7 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %t0, i32 0, i32 3
  %t8 = load i64, ptr %t5
  %t9 = load ptr, ptr %t6
  %t10 = load i64, ptr %t7
  %t11 = lshr i64 %t8, 8
  %t12 = and i64 %t8, 255
  %t13 = icmp ne i64 %t12, 0
  %t14 = zext i1 %t13 to i64
  %t15 = add nuw i64 %t11, %t14
  %t16 = lshr i64 %v0, 8
  %t17 = and i64 %v0, 255
  %t18 = icmp ne i64 %t17, 0
  %t19 = zext i1 %t18 to i64
  %t20 = add nuw i64 %t16, %t19
  br label %paged.v1.start
paged.v1.start:
  br label %paged.v1.size
paged.v1.size:
  %paged.v1.capacity = phi i64 [ %t10, %paged.v1.start ], [ %paged.v1.doubled, %paged.v1.double ]
  %paged.v1.fits = icmp uge i64 %paged.v1.capacity, %t20
  br i1 %paged.v1.fits, label %paged.v1.sized, label %paged.v1.limit
paged.v1.limit:
  %paged.v1.overflow = icmp ugt i64 %paged.v1.capacity, 576460752303423487
  br i1 %paged.v1.overflow, label %paged.oom.v1, label %paged.v1.double
paged.v1.double:
  %paged.v1.doubled = shl nuw i64 %paged.v1.capacity, 1
  br label %paged.v1.size
paged.v1.sized:
  %paged.v1.unchanged = icmp eq i64 %paged.v1.capacity, %t10
  br i1 %paged.v1.unchanged, label %paged.v1.existing, label %paged.v1.resize
paged.v1.resize:
  %t21 = call { i64, i1 } @llvm.umul.with.overflow.i64(i64 %paged.v1.capacity, i64 8)
  %t22 = extractvalue { i64, i1 } %t21, 0
  %t23 = extractvalue { i64, i1 } %t21, 1
  %t24 = call { i64, i1 } @llvm.uadd.with.overflow.i64(i64 %t22, i64 0)
  %t25 = extractvalue { i64, i1 } %t24, 0
  %t26 = extractvalue { i64, i1 } %t24, 1
  %t27 = icmp ugt i64 %t25, 9223372036854775807
  %t28 = or i1 %t23, %t26
  %t29 = or i1 %t28, %t27
  br i1 %t29, label %paged.oom.v1, label %paged.v1.dir.allocate
paged.v1.dir.allocate:
  %t30 = call ptr @malloc(i64 %t25)
  %t31 = icmp ne ptr %t30, null
  br i1 %t31, label %paged.alloc.t30, label %paged.oom.v1
paged.alloc.t30:
  %paged.v1.copied = mul nuw i64 %t15, 8
  call void @llvm.memmove.p0.p0.i64(ptr %t30, ptr %t9, i64 %paged.v1.copied, i1 false)
  call void @free(ptr %t9)
  br label %paged.v1.resized
paged.v1.resized:
  br label %paged.v1.directory
paged.v1.existing:
  br label %paged.v1.directory
paged.v1.directory:
  %paged.v1.dir = phi ptr [ %t30, %paged.v1.resized ], [ %t9, %paged.v1.existing ]
  store ptr %paged.v1.dir, ptr %t6
  store i64 %paged.v1.capacity, ptr %t7
  %paged.v1.no_pages = icmp eq i64 %t15, %t20
  br i1 %paged.v1.no_pages, label %paged.v1.done, label %paged.v1.page.size
paged.v1.page.size:
  %t32 = call { i64, i1 } @llvm.umul.with.overflow.i64(i64 256, i64 16)
  %t33 = extractvalue { i64, i1 } %t32, 0
  %t34 = extractvalue { i64, i1 } %t32, 1
  %t35 = call { i64, i1 } @llvm.uadd.with.overflow.i64(i64 %t33, i64 0)
  %t36 = extractvalue { i64, i1 } %t35, 0
  %t37 = extractvalue { i64, i1 } %t35, 1
  %t38 = icmp ugt i64 %t36, 9223372036854775807
  %t39 = or i1 %t34, %t37
  %t40 = or i1 %t39, %t38
  br i1 %t40, label %paged.oom.v1, label %paged.v1.pages.start
paged.v1.pages.start:
  %t41.empty = icmp eq i64 %t36, 0
  %t41 = select i1 %t41.empty, i64 1, i64 %t36
  br label %paged.v1.pages
paged.v1.pages:
  %paged.v1.page = phi i64 [ %t15, %paged.v1.pages.start ], [ %paged.v1.next, %paged.v1.stored ]
  %paged.v1.finished = icmp eq i64 %paged.v1.page, %t20
  br i1 %paged.v1.finished, label %paged.v1.done, label %paged.v1.allocate
paged.v1.allocate:
  %t42 = call ptr @malloc(i64 %t41)
  %t43 = icmp ne ptr %t42, null
  br i1 %t43, label %paged.alloc.t42, label %paged.oom.v1
paged.alloc.t42:
  %paged.v1.slot = getelementptr inbounds ptr, ptr %paged.v1.dir, i64 %paged.v1.page
  store ptr %t42, ptr %paged.v1.slot
  br label %paged.v1.stored
paged.v1.stored:
  %paged.v1.next = add nuw i64 %paged.v1.page, 1
  br label %paged.v1.pages
paged.oom.v1:
  call void @wf_resource_abort()
  unreachable
paged.v1.done:
  store i64 %v0, ptr %t5
  %v1 = getelementptr i8, ptr %t0, i64 0
  ret ptr %v1
}

define i8 @wf_grow_paged$instance$ed4950029184679a(ptr noalias nonnull captures(none) dereferenceable(8) %v0, i64 %v1) #0 align 64 {
entry:
  %t0 = load ptr, ptr %v0
  %t1 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %t0, i32 0, i32 1
  %t2 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %t0, i32 0, i32 2
  %t3 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %t0, i32 0, i32 3
  %t4 = load i64, ptr %t1
  %t5 = load ptr, ptr %t2
  %t6 = load i64, ptr %t3
  %t7 = lshr i64 %t4, 8
  %t8 = and i64 %t4, 255
  %t9 = icmp ne i64 %t8, 0
  %t10 = zext i1 %t9 to i64
  %t11 = add nuw i64 %t7, %t10
  %t12 = lshr i64 %v1, 8
  %t13 = and i64 %v1, 255
  %t14 = icmp ne i64 %t13, 0
  %t15 = zext i1 %t14 to i64
  %t16 = add nuw i64 %t12, %t15
  br label %paged.v2.start
paged.v2.start:
  br label %paged.v2.size
paged.v2.size:
  %paged.v2.capacity = phi i64 [ %t6, %paged.v2.start ], [ %paged.v2.doubled, %paged.v2.double ]
  %paged.v2.fits = icmp uge i64 %paged.v2.capacity, %t16
  br i1 %paged.v2.fits, label %paged.v2.sized, label %paged.v2.limit
paged.v2.limit:
  %paged.v2.overflow = icmp ugt i64 %paged.v2.capacity, 576460752303423487
  br i1 %paged.v2.overflow, label %paged.oom.v2, label %paged.v2.double
paged.v2.double:
  %paged.v2.doubled = shl nuw i64 %paged.v2.capacity, 1
  br label %paged.v2.size
paged.v2.sized:
  %paged.v2.unchanged = icmp eq i64 %paged.v2.capacity, %t6
  br i1 %paged.v2.unchanged, label %paged.v2.existing, label %paged.v2.resize
paged.v2.resize:
  %t17 = call { i64, i1 } @llvm.umul.with.overflow.i64(i64 %paged.v2.capacity, i64 8)
  %t18 = extractvalue { i64, i1 } %t17, 0
  %t19 = extractvalue { i64, i1 } %t17, 1
  %t20 = call { i64, i1 } @llvm.uadd.with.overflow.i64(i64 %t18, i64 0)
  %t21 = extractvalue { i64, i1 } %t20, 0
  %t22 = extractvalue { i64, i1 } %t20, 1
  %t23 = icmp ugt i64 %t21, 9223372036854775807
  %t24 = or i1 %t19, %t22
  %t25 = or i1 %t24, %t23
  br i1 %t25, label %paged.oom.v2, label %paged.v2.dir.allocate
paged.v2.dir.allocate:
  %t26 = call ptr @malloc(i64 %t21)
  %t27 = icmp ne ptr %t26, null
  br i1 %t27, label %paged.alloc.t26, label %paged.oom.v2
paged.alloc.t26:
  %paged.v2.copied = mul nuw i64 %t11, 8
  call void @llvm.memmove.p0.p0.i64(ptr %t26, ptr %t5, i64 %paged.v2.copied, i1 false)
  call void @free(ptr %t5)
  br label %paged.v2.resized
paged.v2.resized:
  br label %paged.v2.directory
paged.v2.existing:
  br label %paged.v2.directory
paged.v2.directory:
  %paged.v2.dir = phi ptr [ %t26, %paged.v2.resized ], [ %t5, %paged.v2.existing ]
  store ptr %paged.v2.dir, ptr %t2
  store i64 %paged.v2.capacity, ptr %t3
  %paged.v2.no_pages = icmp eq i64 %t11, %t16
  br i1 %paged.v2.no_pages, label %paged.v2.done, label %paged.v2.page.size
paged.v2.page.size:
  %t28 = call { i64, i1 } @llvm.umul.with.overflow.i64(i64 256, i64 16)
  %t29 = extractvalue { i64, i1 } %t28, 0
  %t30 = extractvalue { i64, i1 } %t28, 1
  %t31 = call { i64, i1 } @llvm.uadd.with.overflow.i64(i64 %t29, i64 0)
  %t32 = extractvalue { i64, i1 } %t31, 0
  %t33 = extractvalue { i64, i1 } %t31, 1
  %t34 = icmp ugt i64 %t32, 9223372036854775807
  %t35 = or i1 %t30, %t33
  %t36 = or i1 %t35, %t34
  br i1 %t36, label %paged.oom.v2, label %paged.v2.pages.start
paged.v2.pages.start:
  %t37.empty = icmp eq i64 %t32, 0
  %t37 = select i1 %t37.empty, i64 1, i64 %t32
  br label %paged.v2.pages
paged.v2.pages:
  %paged.v2.page = phi i64 [ %t11, %paged.v2.pages.start ], [ %paged.v2.next, %paged.v2.stored ]
  %paged.v2.finished = icmp eq i64 %paged.v2.page, %t16
  br i1 %paged.v2.finished, label %paged.v2.done, label %paged.v2.allocate
paged.v2.allocate:
  %t38 = call ptr @malloc(i64 %t37)
  %t39 = icmp ne ptr %t38, null
  br i1 %t39, label %paged.alloc.t38, label %paged.oom.v2
paged.alloc.t38:
  %paged.v2.slot = getelementptr inbounds ptr, ptr %paged.v2.dir, i64 %paged.v2.page
  store ptr %t38, ptr %paged.v2.slot
  br label %paged.v2.stored
paged.v2.stored:
  %paged.v2.next = add nuw i64 %paged.v2.page, 1
  br label %paged.v2.pages
paged.oom.v2:
  call void @wf_resource_abort()
  unreachable
paged.v2.done:
  store i64 %v1, ptr %t1
  %v2 = select i1 true, i8 0, i8 0
  %v3 = select i1 true, i8 0, i8 0
  ret i8 %v3
}

define i8 @wf_place_back$instance$dacaeb1c2706d0db(ptr noalias nonnull captures(none) dereferenceable(32) %v0, ptr %wf.arg.v1) #0 align 64 {
entry:
  %wf.slot.0 = alloca %wf.t.79689782061dec13, align 8
  call void @llvm.memmove.p0.p0.i64(ptr %wf.slot.0, ptr %wf.arg.v1, i64 ptrtoint (ptr getelementptr (%wf.t.79689782061dec13, ptr null, i32 1) to i64), i1 false)
  %t1 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v0, i32 0, i32 0
  %t0 = load i64, ptr %t1
  %t2 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v0, i32 0, i32 2
  %t3 = load ptr, ptr %t2
  %t4 = lshr i64 %t0, 8
  %t5 = and i64 %t0, 255
  %t6 = getelementptr inbounds ptr, ptr %t3, i64 %t4
  %t7 = load ptr, ptr %t6
  %t8 = getelementptr inbounds %wf.t.79689782061dec13, ptr %t7, i64 %t5
  call void @llvm.memmove.p0.p0.i64(ptr %t8, ptr %wf.slot.0, i64 ptrtoint (ptr getelementptr (%wf.t.79689782061dec13, ptr null, i32 1) to i64), i1 false)
  %t10 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v0, i32 0, i32 0
  %t9 = load i64, ptr %t10
  %t11 = add i64 %t9, 1
  %t12 = getelementptr inbounds { i64, i64, ptr, i64 }, ptr %v0, i32 0, i32 0
  store i64 %t11, ptr %t12
  %v2 = select i1 true, i8 0, i8 0
  ret i8 %v2
}


define weak i32 @wf__floor_run(i32 %argc, ptr %argv) #0 align 64 {
entry:
  %status = call i32 @wf__main_body(i32 %argc, ptr %argv) noinline
  ret i32 %status
}


attributes #0 = { "probe-stack"="inline-asm" }

declare i8 @wf__ordinary_exit_code(ptr)

define i32 @wf__main_body(i32 %argc, ptr %argv) #0 align 64 {
entry:
  %status = alloca { i128, i128 }, align 16
  call void @"wf_main"(ptr %status)
  %code = call i8 @wf__ordinary_exit_code(ptr %status)
  %exit = zext i8 %code to i32
  ret i32 %exit
}

define i32 @main(i32 %argc, ptr %argv) #0 align 64 {
entry:
  %status = call i32 @wf__floor_run(i32 %argc, ptr %argv)
  ret i32 %status
}
