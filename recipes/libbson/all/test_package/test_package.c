#include <stdio.h>

#include <bson/bson.h>

int
main(void) {
    bson_t *doc = bson_new();
    bson_append_utf8(doc, "hello", -1, "world", -1);
    bson_append_int32(doc, "answer", -1, 42);

    char *json = bson_as_relaxed_extended_json(doc, NULL);
    printf("libbson ok: %s\n", json ? json : "(null)");
    bson_free(json);
    bson_destroy(doc);
    return 0;
}
