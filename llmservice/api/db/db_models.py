import operator

from peewee import BigIntegerField, CharField, CompositeKey, TextField, DateTimeField, BooleanField, Metadata, Model


def remove_field_name_prefix(field_name):
    # 前缀处理，数据库字段比如f_x变为x
    return field_name[2:] if field_name.startswith("f_") else field_name

class BaseModel(Model):
    create_time = BigIntegerField(null=True, index=True)
    create_date = DateTimeField(null=True, index=True)
    update_time = BigIntegerField(null=True, index=True)
    update_date = DateTimeField(null=True, index=True)

    def to_json(self):
        return self.to_dict()

    def to_dict(self):
        # 返回模型的原始数据字典（Peewee底层存储于__data__中）
        return self.__dict__["__data__"]

    def to_human_model_dict(self, only_primary_with:list = None):
        # 指定only_primary_with  只输出主键和额外字段
        model_dict = self.__dict__["__data__"]

        if not only_primary_with :
            return {remove_field_name_prefix(k): v for k, v in model_dict.items()}

        human_model_dict = {}
        #
        for k in self._meta.primary_key.field_names:
            human_model_dict[remove_field_name_prefix(k)] = model_dict[k]
        for k in only_primary_with:
            human_model_dict[k] = model_dict[f"f_{k}"]
        return human_model_dict

    @property
    def meta(self) -> Metadata:
        # 返回模型的meta元数据对象
        return self._meta

    @classmethod
    def get_primary_keys_name(cls):
        # 返回主键名称  isinstance:是否为CompositeKey联合主键类型
        return cls._meta.primary_key.field_names if isinstance(cls._meta.primary_key, CompositeKey) else [cls._meta.primary_key.name]

    @classmethod
    def getter_by(cls, attr):
        # 获取属性访问器
        return operator.attrgetter(attr)(cls)

    @classmethod
    def query(cls, reverse=None, order_by=None, **kwargs):
        """
        动态查询方法，支持常规字段匹配、范围查询、连续字段区间、排序和反向排序。
        reverse: True降序，False升序，None不排序
        order_by: 指定排序字段，若无指定或字段不存在，则默认为create_time
        kwargs: 字段名到查询值映射，支持等值、in、between等
        """
        filters = []
        for f_n, f_v in kwargs.items():
            attr_name = "%s" % f_n
            # 跳过字段不存在或值为None
            if not hasattr(cls, attr_name) or f_v is None:
                continue
            # 支持集合或列表
            if type(f_v) in {list, set}:


class DataBaseModel(BaseModel):
    class Meta:
        database = DB


class User(DataBaseModel, AuthUser):
    id = CharField(max_length=32, primary_key=True)
    access_token = CharField(max_length=255, null=True, index=True)
    nickname = CharField(max_length=100, null=False, help_text="nicky name", index=True)
    password = CharField(max_length=255, null=True, help_text="password", index=True)
    email = CharField(max_length=255, null=False, help_text="email", index=True)
    avatar = TextField(null=True, help_text="avatar base64 string")
    language = CharField(max_length=32, null=True, help_text="English|Chinese", default="Chinese" if "zh_CN" in os.getenv("LANG", "") else "English", index=True)
    color_schema = CharField(max_length=32, null=True, help_text="Bright|Dark", default="Bright", index=True)
    timezone = CharField(max_length=64, null=True, help_text="Timezone", default="UTC+8\tAsia/Shanghai", index=True)
    last_login_time = DateTimeField(null=True, index=True)
    is_authenticated = CharField(max_length=1, null=False, default="1", index=True)
    is_active = CharField(max_length=1, null=False, default="1", index=True)
    is_anonymous = CharField(max_length=1, null=False, default="0", index=True)
    login_channel = CharField(null=True, help_text="from which user login", index=True)
    status = CharField(max_length=1, null=True, help_text="is it validate(0: wasted, 1: validate)", default="1", index=True)
    is_superuser = BooleanField(null=True, help_text="is root", default=False, index=True)

    def __str__(self):
        return self.email

    def get_id(self):
        jwt = Serializer(secret_key=settings.SECRET_KEY)
        return jwt.dumps(str(self.access_token))

    class Meta:
        db_table = "user"