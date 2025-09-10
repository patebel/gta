import torch
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

login_token = "" # generate on hugging face

class HuggingfaceChatAPI:
    def __init__(self, model_id="Qwen/Qwen3-4B-Instruct-2507", n_predict=700, gpu_id=0):
        self.model_id = model_id
        self.n_predict = n_predict
        self.gpu_id = gpu_id

        self.device = self.device_name(gpu_id)

        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            device_map={"": self.device},
            token=login_token
        )

        self.use_chat_template = hasattr(self.tokenizer, "apply_chat_template")
        if not self.use_chat_template:
            self.pipe = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=self.gpu_id if torch.cuda.is_available() else -1,
            )
            self.terminators = [
                self.tokenizer.eos_token_id,
                self.tokenizer.convert_tokens_to_ids("<|eot_id|>")
            ]

        self.system_prompt = (
            "You are a highly specialized sociologist and economist with extensive, "
            "evidence-based knowledge of German cultural, behavioral, and economic patterns. "
            "When given descriptions of specific individuals living in Germany, you must provide detailed, "
            "realistic, and unbiased sociological and economic insights that accurately reflect "
            "contemporary social and economic dynamics. Ensure every output is strictly valid JSON."
        )

    def device_name(self, gpu_id):
        if torch.cuda.is_available():
            return f"cuda:{gpu_id}"
        else:
            return "cpu"

    def get_completion(self, prompt):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        return self._generate_response(messages)

    def get_completions(self, prompts):
        responses = []
        for prompt in prompts:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt},
            ]
            responses.append(self._generate_response(messages))
        return responses

    def _generate_response(self, messages):
        if self.use_chat_template:
            text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            model_inputs = self.tokenizer([text], return_tensors="pt")
            model_inputs = {k: v.to(self.device) for k, v in model_inputs.items()}
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=self.n_predict
            )
            input_length = model_inputs["input_ids"].shape[1]
            trimmed_ids = generated_ids[:, input_length:]
            response = self.tokenizer.batch_decode(trimmed_ids, skip_special_tokens=True)[0]
            return response
        else:
            outputs = self.pipe(
                messages,
                max_new_tokens=self.n_predict,
                eos_token_id=self.terminators,
                do_sample=True,
                temperature=0.6,
                top_p=0.9,
            )
            full_text = outputs[0]["generated_text"][-1]["content"]
            return full_text

if __name__ == "__main__":
    chat = HuggingfaceChatAPI()