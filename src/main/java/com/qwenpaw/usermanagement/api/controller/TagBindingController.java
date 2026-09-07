package com.qwenpaw.usermanagement.api.controller;

import com.qwenpaw.usermanagement.model.dto.TagBindingDTO;
import com.qwenpaw.usermanagement.model.request.BindTagRequest;
import com.qwenpaw.usermanagement.service.TagBindingService;
import org.springframework.web.bind.annotation.*;

/**
 * 标签绑定控制器
 */
@RestController
@RequestMapping("/api/v1/bindings")
public class TagBindingController {

    private final TagBindingService tagBindingService;

    public TagBindingController(TagBindingService tagBindingService) {
        this.tagBindingService = tagBindingService;
    }

    @PostMapping
    public boolean bindTag(@RequestBody BindTagRequest request) {
        return tagBindingService.bindTag(request);
    }

    @DeleteMapping("/{userId}/tags/{tagId}")
    public boolean unbindTag(@PathVariable String userId, @PathVariable String tagId) {
        return tagBindingService.unbindTag(userId, tagId);
    }

    @GetMapping("/{userId}/tags/{tagId}")
    public TagBindingDTO getBinding(@PathVariable String userId, @PathVariable String tagId) {
        return tagBindingService.getBinding(userId, tagId);
    }
}
