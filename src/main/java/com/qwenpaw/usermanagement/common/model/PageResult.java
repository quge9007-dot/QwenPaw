package com.qwenpaw.usermanagement.common.model;

import java.util.List;

/**
 * 分页结果对象
 */
public class PageResult<T> {

    private long total;
    private int page;
    private int pageSize;
    private List<T> records;

    public PageResult() {
    }

    public PageResult(long total, int page, int pageSize, List<T> records) {
        this.total = total;
        this.page = page;
        this.pageSize = pageSize;
        this.records = records;
    }

    public static <T> PageResult<T> of(List<T> records, long total) {
        return new PageResult<>(total, 1, records != null ? records.size() : 0, records);
    }

    public static <T> PageResult<T> empty() {
        return new PageResult<>(0, 1, 0, java.util.Collections.emptyList());
    }

    public long getTotal() {
        return total;
    }

    public void setTotal(long total) {
        this.total = total;
    }

    public int getPage() {
        return page;
    }

    public void setPage(int page) {
        this.page = page;
    }

    public int getPageSize() {
        return pageSize;
    }

    public void setPageSize(int pageSize) {
        this.pageSize = pageSize;
    }

    public List<T> getRecords() {
        return records;
    }

    public void setRecords(List<T> records) {
        this.records = records;
    }
}
