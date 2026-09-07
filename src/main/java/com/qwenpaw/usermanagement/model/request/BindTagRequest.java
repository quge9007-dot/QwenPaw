package com.qwenpaw.usermanagement.model.request;

import jakarta.validation.constraints.NotBlank;

/**
 * 绑定标签请求
 */
public class BindTagRequest {

    @NotBlank(message = "用户ID不能为空")
    private String userId;

    @NotBlank(message = "标签ID不能为空")
    private String tagId;

    private Integer source;

    public String getUserId() {
        return userId;
    }

    public void setUserId(String userId) {
        this.userId = userId;
    }

    public String getTagId() {
        return tagId;
    }

    public void setTagId(String tagId) {
        this.tagId = tagId;
    }

    public Integer getSource() {
        return source;
    }

    public void setSource(Integer source) {
        this.source = source;
    }
}
