# scripts/build_kb2.py — build the KB-2 annotation store (Member 2, Task 4)
from src.knowledge_base.kb2_annotation import AnnotationKB

if __name__ == "__main__":
    AnnotationKB().build()