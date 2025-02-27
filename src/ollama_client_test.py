from ollama import chat
from pydantic import BaseModel

class Pet(BaseModel):
  name: str
  animal: str
  age: int
  color: str | None
  favorite_toy: str | None

class PetList(BaseModel):
  pets: list[Pet]

response = chat(
  messages=[
    {
      'role': 'user',
      'content': '''
        I have two pets.
        Глеб, жук, ему 100 лет, светло-розовый играет с навозом
        I also have a 2 year old black cat named Loki who loves tennis balls.
      ''',
    }
  ],
  model='deepseek-r1:8b', #llama3.2:3b
  format=PetList.model_json_schema(),
)

pets = PetList.model_validate_json(response.message.content)
print(pets)