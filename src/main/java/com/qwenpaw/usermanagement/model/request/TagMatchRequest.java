package com.qwenpaw.usermanagement.model.request;

import jakarta.validation.constraints.NotEmpty;
import java.util.List;

/**
 * 标签匹配请求
 */
public class TagMatchRequest {

    @NotEmpty(message = "标签ID列表不能为空")
    private List<String> tagIds;

    private Integer matchType;

    private Integer page;

    private Integer pageSize;

    public List<String> getTagIds() {
        return tagIds;
    }

    public void setTagIds(List<String> tagIds) {
        this.tagIds = tagIds;
    }

    public Integer getMatchType() {
        return matchType;
    }

    public void setMatchType(Integer matchType) {
        this.matchType = matchType;
    }

    public Integer getPage() {
        return page;
    }

    public void setPage(Integer page) {
        this.page = page;
    }

    public Integer getPageSize() {
        return pageSize;
    }

    public void setPageSize(Integer pageSize) {
        this.pageSize = pageSize;
    }
}
