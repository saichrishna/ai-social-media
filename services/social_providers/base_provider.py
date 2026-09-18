from abc import ABC, abstractmethod


class BaseSocialProvider(ABC):

    @abstractmethod
    def get_authorization_url(
        self,
        state: str
    ) -> str:
        pass


    @abstractmethod
    async def exchange_code(
        self,
        code: str
    ) -> dict:
        pass


    @abstractmethod
    async def get_accounts(
        self,
        access_token: str
    ) -> list:
        pass


    @abstractmethod
    async def publish(
        self,
        post: dict,
        account: dict
    ) -> dict:
        pass